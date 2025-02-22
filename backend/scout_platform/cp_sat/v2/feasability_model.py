from collections import defaultdict
from typing import Optional, Annotated

import re
import numpy as np
import pandas as pd
from ortools.sat.python import cp_model
from pydantic import BaseModel, Field, ConfigDict

from scout_platform.cp_sat.v2.model import GraduationRequirementsSolution, Filter, CourseType, \
    GraduationRequirementsConfig, GraduationRequirementsInstance
from scout_platform.cp_sat.v2.static import all_semesters, Programs

from scout_platform.cp_sat.v2.dependent_variables import (
    TakenBeforeDict,
    AllTakenDict,
    are_all_true,
    TakenBeforeOrConcurrentlyDict,
    TakenAfterDict,
    CreditHourPrerequisiteDict,
    StandingPrerequisiteDict,
    CreditHoursPerSemesterDict, are_any_true, false_var,
)


class FilterConstraintFeas(BaseModel):
    """
    Defaults to all if not specified. filter narrows.
    """

    # uuid: str

    lte: Optional[int] = Field(
        description="maximum credit hours for filters", default=None
    )
    gte: Optional[int] = Field(
        description="minimum credit hours for filters", default=None
    )

    filter: Filter
    name: str


class ProgramMapFeas(BaseModel):
    required_courses: list[str]
    one_of: list[list[str]]
    filter_constraints: list[FilterConstraintFeas]


class GraduationRequirementsInstanceFeas:
    def __init__(self, program_map: ProgramMapFeas, pickle_path: str, semesters: list[str]):
        # specific case
        self.required_courses = program_map.required_courses
        self.one_of = program_map.one_of
        self.filter_constraints = program_map.filter_constraints

        # world
        self.courses: pd.DataFrame = pd.read_pickle(filepath_or_buffer=pickle_path)
        self.courses[["pre_requisites"]].to_html("courses.html")

        self.semester_names: list[str] = semesters


class _CourseVariables:
    def __init__(
            self,
            courses: list[str],
            semesters: list[str],
            course_credit_hours: pd.Series,
            model: cp_model.CpModel,
    ):
        self.course_codes: list[str] = courses
        self.semester_names: list[str] = semesters
        self.model = model

        # unknowns
        self.courses: pd.DataFrame = self._init_unknown_variables()

        # dependent variables
        self.taken_in: pd.Series = self._init_taken_in()
        self.taken: pd.Series = self._init_taken()
        self.taken_as_elective, self.taken_as_core = self._init_taken_as()

        self.all_taken = AllTakenDict(self.model, self.taken)
        self.taken_before = TakenBeforeDict(
            self.model, self.taken_in, self.taken, self.all_taken
        )
        self.taken_concurrently = TakenBeforeOrConcurrentlyDict(
            self.model, self.taken_in, self.taken, self.all_taken
        )

        self.taken_after = TakenAfterDict(
            self.model, self.taken_in, self.taken, self.all_taken
        )

        self.credit_hours_per_semester = CreditHoursPerSemesterDict(
            self.model, self.courses, course_credit_hours
        )

        self.credit_hours_pre_reqisite_met = CreditHourPrerequisiteDict(
            self.model, self.taken_in, self.credit_hours_per_semester
        )

        self.standing_pre_requisite_met = StandingPrerequisiteDict(
            self.model, self.taken, self.taken_in
        )

        self.unknown_prereqs = dict()

    def _init_unknown_variables(self) -> pd.DataFrame:
        variables = np.empty(
            (len(self.course_codes), len(self.semester_names)), dtype=object
        )

        for i, course in enumerate(self.course_codes):
            for j, semester in enumerate(self.semester_names):
                variables[i][j] = self.model.new_bool_var(f"{course}∈{semester}?")

        return pd.DataFrame(
            variables, index=self.course_codes, columns=self.semester_names
        )

    def _init_taken_in(self):
        def func(row: pd.Series) -> cp_model.IntVar:
            var = self.model.new_int_var(lb=0, ub=len(row), name=f"{row.name}_taken_in")
            self.model.add_map_domain(var, row, offset=1)

            # self.model.add(var == (row[]))
            return var

        return self.courses.apply(func, axis=1)

    def _init_taken(self):
        def func(row: pd.Series) -> cp_model.IntVar:
            var = self.model.new_bool_var(name=f"{row.name}_taken?")
            self.model.add_max_equality(var, row)
            return var

        return self.courses.apply(func, axis=1)

    def _init_taken_as(self) -> tuple[pd.Series, pd.Series]:
        def func(row: pd.Series) -> tuple[cp_model.BoolVarT, cp_model.BoolVarT]:
            elective_var = self.model.new_bool_var(name=f"{row.name}∈elective?")
            core_var = self.model.new_bool_var(name=f"{row.name}∈core?")
            course_taken = self.taken[row.name]

            # if the course is taken, it must be a core course or elective course
            self.model.add(sum([core_var, elective_var]) == 1).only_enforce_if(
                course_taken
            )
            self.model.add(course_taken == 1).only_enforce_if(elective_var)
            self.model.add(course_taken == 1).only_enforce_if(core_var)

            return elective_var, core_var

        tmp: pd.Series = self.courses.apply(func, axis=1)
        taken_as_elective = tmp.apply(lambda x: x[0])
        taken_as_core = tmp.apply(lambda x: x[1])
        return taken_as_elective, taken_as_core


class SolverFeedback(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    variable: Annotated[any, Field(exclude=True)]  # cp_model.IntVar, pydantic ignore _ names during serialization step
    category: str
    reason: Optional[str] = None
    lte: Optional[int] = None
    gte: Optional[int] = None
    current: Optional[int] = None
    contributing_courses: Optional[list[str]] = []


class GraduationRequirementsFeasabilitySolver:
    def __init__(
            self,
            problem_instance: GraduationRequirementsInstanceFeas,
            config: GraduationRequirementsConfig,
            completed_classes: list[str]
    ):
        self.problem_instance = problem_instance
        self.config = config
        self.completed_classes = completed_classes
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        self.filter_assumptions_actual = dict()
        self.solver_feedback: list[SolverFeedback] = []

        self._class_vars = _CourseVariables(
            problem_instance.courses.index.values,
            problem_instance.semester_names,
            problem_instance.courses["credit_hours"],
            self.model,
        )

        self._build_model()

    def courses_taken_at_most_once(self, row: pd.Series):
        c = sum(row) <= 1
        course_taken_at_most_once = self.model.new_bool_var(f"{row.name.split("∈")[0]} taken at most once")
        self.model.add(c).only_enforce_if(course_taken_at_most_once)
        # self.assumptions.append(course_taken_at_most_once)

        fdb = SolverFeedback(variable=course_taken_at_most_once,
                             category="Course Taken At Most Once",
                             reason=f"Attempt to take {row.index.name} more than once")

        self.solver_feedback.append(fdb)

        return c

    def limit_courses_per_semester(self, col: pd.Series, limit: int = 5):
        c = sum(col) <= limit
        limit_met = self.model.new_bool_var(f"courses per semester <= {limit}")
        self.model.add(c).only_enforce_if(limit_met)
        # self.assumptions.append(limit_met)

        fdb = SolverFeedback(variable=limit_met,
                             category="Semester Course Limit",
                             reason=f"Attempt to take more than {limit} courses during {col.name}")

        self.solver_feedback.append(fdb)
        return c

    def must_take(self, row: pd.Series):
        # must take as core (test rn)
        course_name = row.name.split("∈")[0]
        taken_as_core = self._class_vars.taken_as_core[course_name]
        v1 = self.model.new_bool_var(f"must take {row.name.split("∈")[0]}")
        c = self.model.add(taken_as_core == 1).only_enforce_if(v1)

        fdb = SolverFeedback(variable=v1,
                             category=row.name.split("∈")[0],
                             reason=f"Required Course Missing")

        self.solver_feedback.append(fdb)

        return c

    def one_of(self, class_options: list[str]):
        # one of these must be taken as core
        one_of_assumption = self.model.new_bool_var(f"one of {', '.join(class_options)} must be taken")
        c = self._class_vars.taken_as_core.loc[class_options].sum() == 1
        self.model.add(c).only_enforce_if(one_of_assumption)
        # self.assumptions.append(one_of_assumption)

        fdb = SolverFeedback(variable=one_of_assumption,
                             category="One of Requirement",
                             reason=f"One of: {", ".join(class_options)} must be taken")

        self.solver_feedback.append(fdb)

    def replace_pre_reqs_with_dvars(
            self, course_code: str, pre_reqs: list[list[str]]
    ) -> (list[list], bool):
        # given something like
        # [CSCI1234U, 30_credit_hours], [CSCI1234U, third_year_standing]
        # replace text with matching variables from model

        patterns = {
            "year_standing": r"^(first|second|third|fourth)_year_standing$",
            "credit_hours": r"^(\d+)_credit_hours$",
            "course_code": r"^[a-z]{3,4}\d{4}u$",
        }

        replaced_pre_reqs: list[list] = []

        for conjunction in pre_reqs:
            acc = []
            for pre_req in conjunction:
                if re.match(patterns["course_code"], pre_req):
                    acc.append(self._class_vars.taken_before[(pre_req, course_code)])

                # no match case, bad expression
            if len(acc) == 0:
                return [], False
            else:
                replaced_pre_reqs.append(acc)

        return replaced_pre_reqs, True

    def apply_pre_requisite(
            self, course: str, prerequisite_options: list[list[str]]
    ) -> bool:

        prerequisite_options_d_vars, ok = self.replace_pre_reqs_with_dvars(
            course, prerequisite_options
        )

        if not ok:
            return False

        course_taken = self._class_vars.taken[course]

        prereqs_taken_before_course = [
            are_all_true(self.model, prequisite_option)
            for prequisite_option in prerequisite_options_d_vars
        ]

        met_prereq_fdb = self.model.new_bool_var("met_prereq_fdb")

        have_prereqs = are_any_true(self.model, prereqs_taken_before_course)

        # if we took the course without the reqs then that is an issue tbqh
        self.model.add(sum([met_prereq_fdb]) == 0).only_enforce_if([~have_prereqs, course_taken])

        fdb = SolverFeedback(variable=met_prereq_fdb,
                             category="Prerequisite Not Met",
                             reason=f"to take {course}, must satisfy:  {prerequisite_options}")
        self.solver_feedback.append(fdb)

        return True

    def collect_filtered_variables(self, f: Filter) -> list[tuple[str, list[any]]]:
        match f.type:
            case CourseType.Elective:
                courses_to_filter = [
                    c
                    for c in zip(
                        self._class_vars.taken_as_elective.index,
                        self._class_vars.taken_as_elective.values,
                    )
                ]
            case CourseType.Core:
                courses_to_filter = [
                    c
                    for c in zip(
                        self._class_vars.taken_as_core.index,
                        self._class_vars.taken_as_core.values,
                    )
                ]
            case CourseType.All:
                courses_to_filter = [
                    c
                    for c in zip(
                        self._class_vars.taken.index,
                        self._class_vars.taken.values,
                    )
                ]
            case _:
                raise Exception("Unhandled CourseType")

        if f.programs:
            courses_to_filter = [
                (course_code, course_taken_var)
                for course_code, course_taken_var in courses_to_filter
                if self.problem_instance.courses.loc[course_code]["program"]
                   in f.programs
            ]

        if f.year_levels:
            courses_to_filter = [
                (course_code, course_taken_var)
                for course_code, course_taken_var in courses_to_filter
                if self.problem_instance.courses.loc[course_code]["year_level"]
                   in f.year_levels
            ]

        if f.course_names:
            courses_to_filter = [
                (course_code, course_taken_var)
                for course_code, course_taken_var in courses_to_filter
                if course_code in f.course_names
            ]

        return courses_to_filter

    def apply_filter_constraint(self, f: FilterConstraintFeas):
        courses_to_filter = self.collect_filtered_variables(f.filter)

        lte_assumption = self.model.new_bool_var(f.name + " lte")
        gte_assumption = self.model.new_bool_var(f.name + " gte")

        # Dependant variable representing the # of credit hours we've taken in this subst of courses
        filter_set_credit_hours = self.model.new_int_var(
            lb=0, ub=10_000, name="filter_set_credit_hours"
        )
        # bind value to d-var
        # NOTE: everything is scaled here because ortools can't handle floats and some classes have 1.5 hours
        SCALE_FACTOR = 10
        self.model.add(
            filter_set_credit_hours
            == sum(
                [
                    SCALE_FACTOR
                    * int(self.problem_instance.courses.loc[code]["credit_hours"])
                    * course_taken
                    for code, course_taken in courses_to_filter
                ]
            )
        )

        if f.lte:
            self.model.add(filter_set_credit_hours <= SCALE_FACTOR * f.lte).only_enforce_if(lte_assumption)
            self.filter_assumptions_actual[f.name + " lte"] = filter_set_credit_hours

            fdb = SolverFeedback(variable=lte_assumption,
                                 category=f.name,
                                 reason=f"maximum of {f.lte} credit hours",
                                 current=-1
                                 # using this as a bad way to indicate that this needs to be populated post solve (not None)
                                 )
            self.solver_feedback.append(fdb)
        if f.gte:
            self.model.add(filter_set_credit_hours >= SCALE_FACTOR * f.gte).only_enforce_if(gte_assumption)
            self.filter_assumptions_actual[f.name + " gte"] = filter_set_credit_hours

            fdb = SolverFeedback(variable=gte_assumption,
                                 category=f.name,
                                 reason=f"{f.gte}+ credit hours",
                                 current=-1
                                 # using this as a bad way to indicate that this needs to be populated post solve (not None)
                                 )
            self.solver_feedback.append(fdb)

    def set_taken_courses(self):
        for course_code, taken_var in self._class_vars.taken.items():
            issue_taking_course = self.model.new_bool_var("issue taking course")
            if str(course_code).upper() in self.completed_classes:
                self.model.add(taken_var == 1) #.only_enforce_if(issue_taking_course)
                # fdb = SolverFeedback(variable=issue_taking_course,
                #                      category="issue taking course (set to 1)",
                #                      reason=f"unable to take {course_code}",
                #                      )
                # self.solver_feedback.append(fdb)
            else:
                self.model.add(taken_var == 0) #.only_enforce_if(issue_taking_course)
                #
                # fdb = SolverFeedback(variable=issue_taking_course,
                #                      category="issue taking course (set to 0)",
                #                      reason=f"unable to take {course_code}",
                #                      )
                # self.solver_feedback.append(fdb)

    def _add_constraints(self):
        self.set_taken_courses()

        self._class_vars.courses.apply(self.limit_courses_per_semester, axis=0)

        self._class_vars.courses.apply(self.courses_taken_at_most_once, axis=1)

        self._class_vars.taken_as_core[self.problem_instance.required_courses].apply(
            self.must_take
        )

        for option in self.problem_instance.one_of:
            self.one_of(option)


        for course_code, prerequisite_options in zip(
                self.problem_instance.courses.index,
                self.problem_instance.courses["pre_requisites"].values,
        ):
            if prerequisite_options:
                self.apply_pre_requisite(course_code, prerequisite_options)

        for filter_constraint in self.problem_instance.filter_constraints:
            self.apply_filter_constraint(filter_constraint)

    def _build_model(self):
        self._add_constraints()

        # maximize how many are true, false assumptions are invalid model states
        self.model.maximize(sum([feedback.variable for feedback in self.solver_feedback]))

    def take_class_in(self, class_name: str, semester: int):
        class_name = class_name.lower()
        assert 1 <= semester <= 9, "only 8 semesters (1->9)"

        # fdb = self.model.new_bool_var("take class in sem")
        self.model.add(self._class_vars.taken_in.loc[class_name] == semester)  # .only_enforce_if(fdb)

        # fdb = SolverFeedback(variable=fdb,
        #                      category="Take Class In",
        #                      reason=f"Unable to take {class_name} in semester {semester}",
        #                      )
        # self.solver_feedback.append(fdb)

    def solve(self) -> list[SolverFeedback]:
        self.solver.parameters.max_time_in_seconds = self.config.time_limit
        # self.solver.parameters.relative_gap_limit = self.config.opt_tol
        self.solver.parameters.relative_gap_limit = 0.001  # TODO: test

        status = self.solver.solve(self.model)
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            if status == cp_model.OPTIMAL:
                print("[FEAS MODEL] OPTIMAL", self.solver.objective_value)
            else:
                print("[FEAS MODEL] FEASIBLE", self.solver.objective_value)

            courses_taken = defaultdict(list)

            # print("========================")
            # for course in self.completed_classes:
            #     is_elective = self.solver.value(self._class_vars.taken_as_elective[course.lower()])
            #     is_core = self.solver.value(self._class_vars.taken_as_core[course.lower()])
            #     print(course, end="")
            #     if is_elective:
            #         print("_E")
            #     if is_core:
            #         print("_C")

            res = []

            for feedback in self.solver_feedback:
                if self.solver.value(feedback.variable) == 0:
                    # if True:
                    print(feedback)
                    if feedback.current == -1:
                        feedback.current = 1337

                        for fltr in self.problem_instance.filter_constraints:
                            if fltr.name == feedback.category:
                                print("MATCH")
                                variables = self.collect_filtered_variables(fltr.filter)
                                total = 0
                                contributing_courses = []
                                for course_code, taken_var in variables:
                                    if self.solver.value(taken_var) == 1:
                                        total += 3  # variable # of credit hours exist, this is hardcoded, bad
                                        contributing_courses.append(course_code)
                                feedback.current = total
                                feedback.contributing_courses = contributing_courses
                                feedback.gte = fltr.gte
                                feedback.lte = fltr.lte

                    res.append(feedback)

            return res

        else:
            print("feas_model INFEASIBLE")
            return [SolverFeedback(variable=false_var(self.model), category="Infeasible Model",
                                   reason="Something went wrong on our end")]


def get_cs_program_map_feas() -> ProgramMapFeas:
    min_elective_ch = FilterConstraintFeas(name="Electives", gte=45, filter=Filter(type=CourseType.Elective))

    # No more than 42 credit hours may be taken at the first-year level
    max_42_credit_hours_at_first_year_level = FilterConstraintFeas(
        name="first year courses <= 42",
        lte=42, filter=Filter(year_levels=[1], type=CourseType.All)
    )

    # Students are required to complete at least 12 credit hours in Computer Science courses at the 4000 level
    year_4_cs_min_12ch = FilterConstraintFeas(
        name="4th Year CS Courses",
        gte=12,
        filter=Filter(
            programs=[Programs.computer_science],
            year_levels=[4],
            type=CourseType.All,
        ),
    )

    science = [
        Programs.biology,
        Programs.chemistry,
        Programs.computer_science,
        Programs.environmental_science,
        Programs.forensic_science,
        Programs.neuroscience,
        Programs.physics,
        Programs.statistics,
    ]
    # 27 credit hours must be in courses offered by the Faculty of Science
    min_27ch_science = FilterConstraintFeas(
        name="Science Electives",
        gte=27, filter=Filter(type=CourseType.Elective, programs=science)
    )

    # at least 12 credit hours must be in Senior Computer Science electives, with no more than 15 credit hours being in Computer Science
    year_4_cs_min_12ch_max_15ch = FilterConstraintFeas(
        name="Senior CS Electives",
        lte=15,
        gte=12,
        filter=Filter(
            programs=[Programs.computer_science],
            year_levels=[4],
            type=CourseType.Elective,
        ),
    )

    cs_program_map = ProgramMapFeas(
        required_courses=[
            "csci1030u",
            "csci1060u",
            "csci1061u",
            "csci2050u",
            "math1020u",
            "phy1020u",
            "csci2000u",
            "csci2010u",
            "csci2020u",
            "csci2040u",
            "csci2072u",
            "csci2110u",
            "math2050u",
            "stat2010u",
            "csci3070u",
            "csci4040u",
        ],
        one_of=[
            ["phy1010u", "phy1030u"],
            ["math1010u", "math1000u"],
            ["csci3010u", "csci3030u", "csci4030u", "csci4050u", "csci4610u"],
            ["csci3090u", "csci4110u", "csci4210u", "csci4220u"],
            ["csci3230u", "csci4100u", "csci4160u", "csci4620u"],
            ["csci3055u", "csci3060u", "csci4020u", "csci4060u"],
            ["csci3020u", "csci3150u", "csci3310u", "csci4310u"],
            [
                "busi1600u",
                "busi1700u",
                "busi2000u",
                "busi2200u",
                "busi2311u",
            ],
            [
                "comm1050u",
                "comm1100u",
                "comm1320u",
                "comm2311u",
                "comm2620u",
            ],
        ],
        filter_constraints=[
            min_elective_ch,
            max_42_credit_hours_at_first_year_level,
            year_4_cs_min_12ch,
            min_27ch_science,
            year_4_cs_min_12ch_max_15ch,
        ],
    )

    return cs_program_map


if __name__ == "__main__":
    cs_map = get_cs_program_map_feas()

    gr_instance = GraduationRequirementsInstanceFeas(
        program_map=cs_map,
        semesters=all_semesters,
        pickle_path="uoit_courses.pickle",
    )

    # 1st year core
    completed_classes = ["csci1030u", "csci1060u", "csci1061u", "csci2050u", "math1020u",
                         "phy1020u", "math1000u", "phy1010u"]  # + 2 electives

    # 2nd year core
    completed_classes += ["csci2000u", "csci2010u", "csci2020u", "csci2040u", "csci2072u",
                          "csci2110u", "math2050u", "stat2010u"]  # + 2 electives

    # 3/4 core
    completed_classes += ["csci3070u", ""]  # + 7 electives, 4 cs electives
    # one of
    completed_classes += ["csci3010u"]
    completed_classes += ["csci3090u"]
    completed_classes += ["csci3230u"]
    completed_classes += ["csci3055u"]
    # completed_classes += ["csci3020u"]

    # completed_classes += ["csci4040u"]

    completed_classes += ["busi1600u"]
    completed_classes += ["comm1050u"]

    completed_classes += ["biol1000u"]
    completed_classes += ["biol1010u"]

    solver = GraduationRequirementsFeasabilitySolver(
        problem_instance=gr_instance,
        config=GraduationRequirementsConfig(print_stats=False),
        completed_classes=completed_classes
    )

    out = solver.solve()

    for thing in out:
        print(thing.category, "|", thing.reason, end="")
        if thing.current is not None:
            print(f" | actual: {thing.current} | ", end="")
            print(f"contrib: {thing.contributing_courses} ")
        else:
            print("")
