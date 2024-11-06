import logging
from collections import defaultdict
from enum import Enum
from typing import Optional
from dependent_variables import TakenBeforeDict, AllTakenDict, are_all_true

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
    all_courses,
)
from solver.v2.util import course_level, get_code, print_statistics
from parser.csv_parser import CourseCsvParser, Course


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
    program: Optional[list[str]] = None
    year_levels: Optional[list[PositiveInt]] = None
    type: Optional[CourseType] = CourseType.Elective


class ProgramMap(BaseModel):
    required_courses: list[str]
    one_of: list[list[str]]
    filter_constraints: list[FilterConstraint]


class GraduationRequirementsInstance:
    def __init__(
        self,
        program_map: ProgramMap,
        courses: list[str],
        semesters: list[str],
        prerequisites: dict[str, list[str]],
        cross_listed: dict[str, list[str]],
    ):
        # specific case
        self.required_courses = program_map.required_courses
        self.one_of = program_map.one_of
        self.filter_constraints = program_map.filter_constraints

        # world
        self.course_codes: list[str] = courses
        self.semester_names: list[str] = semesters
        self.prerequisites: dict[str, list[str]] = prerequisites
        self.cross_listed: dict[str, list[str]] = cross_listed


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
        csv_path: str,
    ):
        # TODO: parse and read csv or db, use that to create variables

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
            problem_instance.course_codes, problem_instance.semester_names, self.model
        )

        self.logger.debug("%s courses", len(self._class_vars.courses.index))
        self.logger.debug("%s semesters", len(self._class_vars.courses.columns))

        self._build_model()

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

        def apply_cross_listed():
            for course in self.problem_instance.cross_listed.keys():
                courses = [course, *self.problem_instance.cross_listed[course]]
                courses = list(filter(lambda x: x in all_courses, courses))
                courses_taken_vars = self._class_vars.taken.loc[courses].values
                self.model.add_at_most_one(courses_taken_vars)

        apply_cross_listed()

        def apply_pre_requisite(course: str, prerequisite_options: list[str]):
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

        for course, prerequisite_options in self.problem_instance.prerequisites.items():
            apply_pre_requisite(course, prerequisite_options)

        def apply_filter_constraint(f: FilterConstraint):
            # TODO: i need to read the csv and include metadata
            #  about courses in there instead of parsing course codes

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

            if f.program:
                courses_to_filter = [
                    (course_code, course_taken_var)
                    for course_code, course_taken_var in courses_to_filter
                    if get_code(course_code) in f.program
                ]

            if f.year_levels:
                courses_to_filter = [
                    (course_code, course_taken_var)
                    for course_code, course_taken_var in courses_to_filter
                    if course_level(course_code) in f.year_levels
                ]

            filtered_courses = [c for _, c in courses_to_filter]

            # might be bad to assume that courses are all 3 credit hours
            COURSE_CREDIT_HOURS = 3
            if f.lte:
                self.model.add(sum(filtered_courses) <= (f.lte // COURSE_CREDIT_HOURS))
            if f.gte:
                self.model.add(sum(filtered_courses) >= (f.gte // COURSE_CREDIT_HOURS))

        for filter_constraint in self.problem_instance.filter_constraints:
            apply_filter_constraint(filter_constraint)

    def _build_model(self):
        self._add_constraints()
        self.model.minimize(sum(self._class_vars.courses.values.flatten()))

    def solve(self) -> GraduationRequirementsSolution:
        self.solver.parameters.max_time_in_seconds = self.config.time_limit
        self.solver.parameters.relative_gap_limit = self.config.opt_tol

        status = self.solver.solve(self.model)
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            courses_taken = defaultdict(list)
            for i, v in enumerate(self._class_vars.taken_in.values):
                class_name = self._class_vars.taken_in.index.tolist()[i]
                value = self.solver.value(v)
                if value != 0:
                    courses_taken[value].append(
                        class_name
                        + f"_({"E" if self.solver.value(self._class_vars.taken_as_elective[class_name]) else "C"})"
                    )

            if self.config.print_stats:
                print_statistics(self.solver)
            return GraduationRequirementsSolution(taken_courses=courses_taken)
        else:
            print(f"No Solution {self.solver.status_name()}")
            if self.config.print_stats:
                print_statistics(self.solver)
            return GraduationRequirementsSolution(taken_courses=dict())

    def take_class(self, class_name: str):
        self.model.add(self._class_vars.taken[class_name] == 1)
