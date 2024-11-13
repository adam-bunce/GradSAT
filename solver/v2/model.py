import logging
from collections import defaultdict
from enum import Enum
from typing import Optional
from dependent_variables import (
    TakenBeforeDict,
    AllTakenDict,
    are_all_true,
    TakenBeforeOrConcurrentlyDict,
    TakenAfterDict,
)

import numpy as np
from pydantic import (
    BaseModel,
    Field,
    PositiveFloat,
    PositiveInt,
    NonNegativeFloat,
)
from ortools.sat.python import cp_model
import pandas as pd

from solver.v2.static import (
    int_to_semester,
    Programs,
)
from solver.v2.util import print_statistics
from parser.csv_parser import CourseCsvParser


class CourseType(Enum):
    Elective = "Elective"
    Core = "Core"
    All = "All"


class FilterConstraint(BaseModel):
    """
    Defaults to all if not specified. filter narrows.
    """

    lte: Optional[int] = Field(
        description="maximum credit hours for filters", default=None
    )
    gte: Optional[int] = Field(
        description="minimum credit hours for filters", default=None
    )
    programs: Optional[list[Programs]] = None
    year_levels: Optional[list[PositiveInt]] = None
    type: Optional[CourseType] = CourseType.Elective


class ProgramMap(BaseModel):
    required_courses: list[str]
    one_of: list[list[str]]
    filter_constraints: list[FilterConstraint]


class GraduationRequirementsInstance:
    def __init__(self, program_map: ProgramMap, pickle_path: str, semesters: list[str]):
        # specific case
        self.required_courses = program_map.required_courses
        self.one_of = program_map.one_of
        self.filter_constraints = program_map.filter_constraints

        # TODO; fix rows that are badly formatted
        # world
        self.courses: pd.DataFrame = pd.read_pickle(filepath_or_buffer=pickle_path)
        self.courses[["pre_requisites"]].to_html("courses.html")

        self.semester_names: list[str] = semesters


class GraduationRequirementsConfig(BaseModel):
    time_limit: PositiveFloat = Field(default=5.0, description="Time limit in seconds.")
    opt_tol: NonNegativeFloat = Field(
        default=0.01, description="Optimality tolerance (1% gap allowed)."
    )
    log_model_building: bool = Field(
        default=False, description="Whether to log the building progress."
    )
    print_stats: bool = Field(default=False, description="display search stats")


class GraduationRequirementsSolution(BaseModel):
    taken_courses: dict[int, list[str]]

    def __str__(self):
        if len(self.taken_courses) == 0:
            return "no courses taken."

        total_courses_taken = sum(map(len, self.taken_courses.values()))
        buf = f"took {total_courses_taken} courses\n"
        for semester in sorted(self.taken_courses.keys()):
            buf += f"{int_to_semester[semester]:9}: "
            for course in self.taken_courses[semester]:
                buf += f"{course:13} "
            buf += "\n"

        return buf


class _CourseVariables:
    def __init__(
        self,
        courses: list[str],
        semesters: list[str],
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


class GraduationRequirementsSolver:
    def __init__(
        self,
        problem_instance: GraduationRequirementsInstance,
        config: GraduationRequirementsConfig,
    ):
        self.problem_instance = problem_instance
        self.config = config
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()

        logging.basicConfig(
            format="%(asctime)s %(levelname)s:%(message)s",
            level=logging.DEBUG,
            datefmt="%m/%d/%Y %H:%M:%S %z",
        )
        self.logger = logging.getLogger(__name__)

        self._class_vars = _CourseVariables(
            problem_instance.courses.index.values,
            problem_instance.semester_names,
            self.model,
        )

        self.logger.debug("%s courses", len(self._class_vars.courses.index))
        self.logger.debug("%s semesters", len(self._class_vars.courses.columns))

        self._build_model()

    def validate_program_map(self) -> bool:
        courses = [
            course
            for course_list in self.problem_instance.one_of
            for course in course_list
        ] + self.problem_instance.required_courses
        return len(self.problem_instance.courses.loc[courses]) == len(courses)

    def _add_constraints(self):
        def courses_taken_at_most_once(row: pd.Series):
            c = sum(row) <= 1
            self.model.add(c)
            return c

        self._class_vars.courses.apply(courses_taken_at_most_once, axis=1)

        def limit_courses_per_semester(col: pd.Series):
            LIMIT = 5
            c = sum(col) <= LIMIT
            self.model.add(c)
            return c

        self._class_vars.courses.apply(limit_courses_per_semester, axis=0)

        def must_take(row: pd.Series):
            c = row == 1
            self.model.add(c)
            return c

        self._class_vars.taken_as_core[self.problem_instance.required_courses].apply(
            must_take
        )

        def one_of(class_options: list[str]):
            # one of these must be taken as core
            c = self._class_vars.taken_as_core.loc[class_options].sum() == 1
            self.model.add(c)

        for option in self.problem_instance.one_of:
            one_of(option)

        def apply_credit_restrictions(course: str, restrictions: list[str]):
            course_codes = [course, *restrictions[0]]
            course_codes = list(
                filter(
                    lambda x: x in self._class_vars.courses.index.values, course_codes
                )
            )
            courses_taken_vars = self._class_vars.taken.loc[course_codes].values
            self.model.add_at_most_one(courses_taken_vars)

        for course, restrictions in zip(
            self.problem_instance.courses.index,
            self.problem_instance.courses["credit_restrictions"],
        ):
            if restrictions:
                apply_credit_restrictions(course, restrictions)

        unhandled_pre_reqs: dict[str, str] = dict()

        def apply_pre_requisite(course: str, prerequisite_options: list[list[str]]):
            for opts in prerequisite_options:
                for opt in opts:
                    # not a course code, something else
                    if len(opt) > 9:
                        print(course, prerequisite_options)
                        # should be one thing if it failed to parse
                        unhandled_pre_reqs[course] = prerequisite_options[0][0]
                        return

            course_taken = self._class_vars.taken[course]

            prereqs_taken_before_course = [
                are_all_true(
                    self.model,
                    [
                        self._class_vars.taken_before[(prereq, course)]
                        for prereq in prequisite_option
                    ],
                )
                for prequisite_option in prerequisite_options
            ]

            # one of the pre-req combos must be met if we're going to take the course
            self.model.add_at_least_one(prereqs_taken_before_course).only_enforce_if(
                course_taken
            )

        for course_code, prerequisite_options in zip(
            self.problem_instance.courses.index,
            self.problem_instance.courses["pre_requisites"].values,
        ):
            if prerequisite_options:
                apply_pre_requisite(course_code, prerequisite_options)

        print("====================\n", len(unhandled_pre_reqs), unhandled_pre_reqs)

        def apply_unknown_prerequisites(course: str, unknown_pre_req: str):
            course_taken = self._class_vars.taken[course_code]
            prereq_met = self.model.new_bool_var(f"met_{unknown_pre_req}")
            # if we take this course, whatever this is must be met
            self.model.add(prereq_met == 1).only_enforce_if(course_taken)
            self._class_vars.unknown_prereqs[course] = prereq_met

        for course, unknown_prereq in unhandled_pre_reqs.items():
            apply_unknown_prerequisites(course, unknown_prereq)

        self.model.add(self._class_vars.unknown_prereqs["biol4080u"] == 0)

        def apply_co_requisite(course_code: str, co_requisite_options: list[list[str]]):
            course_taken = self._class_vars.taken[course_code]

            met_co_requisites = [
                are_all_true(
                    self.model,
                    [
                        self._class_vars.taken_concurrently[(coreq, course)]
                        for coreq in coreq_option
                    ],
                )
                for coreq_option in co_requisite_options
            ]

            # one of the co-req combos must be met if we're going to take the course
            self.model.add_at_least_one(met_co_requisites).only_enforce_if(course_taken)

        for course_code, co_requisite_option in zip(
            self.problem_instance.courses.index,
            self.problem_instance.courses["co_requisites"].values,
        ):
            if co_requisite_option:
                apply_co_requisite(course_code, co_requisite_option)

        def apply_post_requisite(
            course_code: str, post_requisite_options: list[list[str]]
        ):
            course_taken = self._class_vars.taken[course_code]

            met_post_requisites = [
                are_all_true(
                    self.model,
                    [
                        self._class_vars.taken_after[(post_req, course_code)]
                        for post_req in post_req_option
                    ],
                )
                for post_req_option in post_requisite_options
            ]

            # one of the post-req combos must be met if we're going to take the course
            self.model.add_at_least_one(met_post_requisites).only_enforce_if(
                course_taken
            )

        # TODO: need to manually add column to csv
        for course_code, post_requisites in [
            ("csci4410u", [["csci4420u"]]),
            # self.problem_instance.courses.index,
            # self.problem_instance.courses["co_requisites"].values,
        ]:
            if post_requisites:
                print("applying post requisite", course_code, post_requisites)
                apply_post_requisite(course_code, post_requisites)

        def minimum_year_constraint(course_code: str, year: int):
            year_to_sem: dict[int, list[int]] = {
                1: [1, 2],
                2: [3, 4],
                3: [5, 6],
                4: [7, 8],
            }

            min_semester = year_to_sem[year][0]
            course_taken_in = self._class_vars.taken_in.loc[course_code]
            self.model.add(course_taken_in >= min_semester)

        # TODO: add column to csv for this
        # need to be third year to take 4040
        minimum_year_constraint("csci4040u", 3)

        def apply_filter_constraint(f: FilterConstraint):
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
                self.model.add(filter_set_credit_hours <= SCALE_FACTOR * f.lte)
            if f.gte:
                self.model.add(filter_set_credit_hours >= SCALE_FACTOR * f.gte)

        for filter_constraint in self.problem_instance.filter_constraints:
            apply_filter_constraint(filter_constraint)

        def apply_minimum_year_standing():
            pass

    def _build_model(self):
        self._add_constraints()
        self.model.minimize(sum(self._class_vars.courses.values.flatten()))
        # minimize assumptions made
        self.model.minimize(sum(self._class_vars.unknown_prereqs.values()))

    def solve(self) -> GraduationRequirementsSolution:
        self.solver.parameters.max_time_in_seconds = self.config.time_limit
        self.solver.parameters.relative_gap_limit = self.config.opt_tol

        status = self.solver.solve(self.model)
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            courses_taken_just_codes: list[str] = []
            courses_taken = defaultdict(list)
            for i, v in enumerate(self._class_vars.taken_in.values):
                class_name = self._class_vars.taken_in.index.tolist()[i]
                value = self.solver.value(v)
                if value != 0:
                    courses_taken[value].append(
                        class_name
                        + f"_({"E" if self.solver.value(self._class_vars.taken_as_elective[class_name]) else "C"})"
                    )

                    courses_taken_just_codes.append(class_name)

            if self.config.print_stats:
                print_statistics(self.solver)

            print("Assumptions:")
            for course, prereq in self._class_vars.unknown_prereqs.items():
                if course in courses_taken_just_codes:
                    if self.solver.value(prereq) == 1:
                        print(course, "->", prereq)

            return GraduationRequirementsSolution(taken_courses=courses_taken)
        else:
            print(f"No Solution {self.solver.status_name()}")
            if self.config.print_stats:
                print_statistics(self.solver)
            return GraduationRequirementsSolution(taken_courses=dict())

    def take_class(self, class_name: str):
        self.model.add(self._class_vars.taken[class_name] == 1)
