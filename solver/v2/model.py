import csv
import logging
from enum import Enum
from typing import Optional

import numpy as np
from pydantic import (
    BaseModel,
    Field,
    constr,
    PositiveFloat,
    NonNegativeInt,
    PositiveInt,
    NonNegativeFloat,
)
from ortools.sat.python import cp_model
import pandas as pd

from solver.v2.static import all_courses, all_semesters, prerequisites

logging.basicConfig(
    format="%(asctime)s %(levelname)s:%(message)s",
    level=logging.DEBUG,
    datefmt="%m/%d/%Y %H:%M:%S %z",
)
_logger = logging.getLogger(__name__)


class Programs(Enum):
    academic_learning_and_success = "Academic Learning and Success"
    automotive_engineering = "Automotive Engineering"
    biology = "Biology"
    business = "Business"
    chemistry = "Chemistry"
    communication = "Communication"
    computer_science = "Computer Science"
    criminology_and_justice = "Criminology and Justice"
    curriculum_studies = "Curriculum Studies"
    economics = "Economics"
    education = "Education"
    esadt = "Educational Studies and Digital Technology"
    electrical_engineering = "Electrical Engineering"
    energy_sys_and_nuclear = "Energy Systems and Nuclear Science"
    engineering = "Engineering"
    environmental_science = "Environmental Science"
    forensic_psychology = "Forensic Psychology"
    forensic_science = "Forensic Science"
    health_science = "Health Science"
    indigenous = "Indigenous"
    information_technology = "Information Technology"
    integrated_mathematics_and_computer_science = (
        "Integrated Mathematics and Computer Science"
    )
    kinesiology = "Kinesiology"
    legal_studies = "Legal Studies"
    liberal_studies = "Liberal Studies"
    manufacturing_engineering = "Manufacturing Engineering"
    mathematics = "Mathematics"
    mechanical_engineering = "Mechanical Engineering"
    mechatronics_engineering = "Mechatronics Engineering"
    medical_laboratory_science = "Medical Laboratory Science"
    neuroscience = "Neuroscience"
    nuclear = "Nuclear"
    nursing = "Nursing"
    physics = "Physics"
    political_science = "Political Science"
    psychology = "Psychology"
    radiation_science = "Radiation Science"
    science = "Science"
    science_coop = "Science Co-op"
    social_science = "Social Science"
    sociology = "Sociology"
    software_engineering = "Software Engineering"
    statistics = "Statistics"
    sustainable_energy_systems = "Sustainable Energy Systems"


class Course(BaseModel):
    year_level: int = Field(description="the year level of the course; 1,2,3,4")
    program: Programs = Field(description="program the course is part of")
    course_prefix: constr(min_length=3, max_length=4)
    course_code: constr(min_length=5, max_length=5)
    course_name: str

    credit_hours: NonNegativeFloat
    lecture_hours: NonNegativeFloat
    laboratory_hours: NonNegativeFloat
    tutorial_hours: NonNegativeFloat

    # DNF list (1030 and 1050) or 1060
    credit_restrictions: list[list[str]]
    pre_requisites: list[list[str]]
    post_requisites: list[list[str]]
    pre_requisites_with_concurrency: list[list[str]]
    co_requisites: list[list[str]]
    credit_restrictions: list[list[str]]

    def __str__(self) -> str:
        return f"{self.course_name} ({self.course_prefix}{str(self.course_code)})"


# maybe there's a way to filter a dataframe like this easier?
class CourseFilter(BaseModel):
    lt: Optional[int] = Field(
        description="maximum credit hours for filters", default=None
    )
    gt: Optional[int] = Field(
        descriptino="minimum credit hours for filters", default=None
    )
    program: Optional[list[Programs]] = None
    year_levels: Optional[list[PositiveInt]] = None


# i forget why i made this?
# class CourseFilters(BaseModel):
#     count: int
#     course_filter: CourseFilter


# antlr DSL seems better than this (if i'm generalizing)
# TODO: finish this class.
#   then start working on the instance
#   then the solver
class ProgramMap(BaseModel):
    # TODO: repalce with course obj
    required_courses: list[str]
    one_of: list[list[str]]
    min_of_type: list[CourseFilter]
    max_of_type: list[CourseFilter]
    min_electives: int


# instance of the problem
class GraduationRequirementsInstance:
    def __init__(self, program_map: ProgramMap):
        self.required_courses = program_map.required_courses
        self.one_of = program_map.one_of
        self.min_of_type = program_map.min_of_type
        self.max_of_type = program_map.max_of_type
        self.min_electives = program_map.min_electives

        # wrong, could have overlap
        self.total_courses = (
            len(self.required_courses)
            + len(self.one_of)
            + len(self.min_of_type)
            + self.min_electives
        )


class GraduationRequirementsConfig(BaseModel):
    time_limit: PositiveFloat = Field(
        default=60.0, description="Time limit in seconds."
    )
    opt_tol: NonNegativeFloat = Field(
        default=0.01, description="Optimality tolerance (1% gap allowed)."
    )
    log_search_progress: bool = Field(
        default=False, description="Whether to log the search progress."
    )


class GraduationRequirementsSolution(BaseModel):
    taken_courses: tuple[str, int]


# keep meta data about courses separate and do lookups using index of panda db (course str name)
# have dependent variables in other variables and create lookup functions to use them
class _CourseVariables:
    def __init__(
        self,
        instance: GraduationRequirementsInstance,
        model: cp_model.CpModel,
    ):
        self.instance = instance
        self.model = model

        # unknowns
        self.courses: pd.DataFrame = self._init_unknown_variables()

        # dependant variables
        self.taken_in: pd.Series = self._init_taken_in()
        self.taken: pd.Series = self._init_taken()

    def _init_unknown_variables(self) -> pd.DataFrame:
        variables = np.empty((len(all_courses), len(all_semesters)), dtype=object)

        for i, course in enumerate(all_courses):
            for j, semester in enumerate(all_semesters):
                variables[i][j] = self.model.new_bool_var(f"{course}∈{semester}?")

        return pd.DataFrame(variables, index=all_courses, columns=all_semesters)

    def _init_taken_in(self):
        def func(row: pd.Series) -> cp_model.IntVar:
            var = self.model.new_int_var(
                lb=0, ub=len(row) + 1, name=f"{row.name}_taken_in"
            )
            self.model.add_map_domain(var, row, offset=1)
            return var

        return self.courses.apply(func, axis=1)

    def _init_taken(self):
        def func(row: pd.Series) -> cp_model.IntVar:
            var = self.model.new_bool_var(name=f"{row.name}_taken")
            self.model.add_max_equality(var, row)
            return var

        return self.courses.apply(func, axis=1)

    def get_courses_variables(self, course_list: list[str]) -> pd.DataFrame:
        return self.courses.loc[course_list]

    def get_course_taken_in(self, course: str) -> cp_model.IntVar:
        return self.taken_in.loc[course]

    def get_course_taken(self, course: str) -> cp_model.BoolVarT:
        return self.taken.loc[course]


# thing to solve the problem
class GraduationRequirementsSolver:
    def __init__(
        self,
        instance: GraduationRequirementsInstance,
        config: GraduationRequirementsConfig,
        csv_path: str,
    ):
        self.instance = instance
        self.config = config
        self.model = cp_model.CpModel()
        self.solver = cp_model.CpSolver()
        self.tmp = []

        # TODO: parse and read csv or db, use that to create variables

        self._class_vars = _CourseVariables(instance, self.model)
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

        self.model.add(sum(self._class_vars.courses.values.flatten()) > 30)

        def must_take(row: pd.Series):
            c = sum(row) >= 1
            self.model.add(c)
            return c

        self._class_vars.get_courses_variables(self.instance.required_courses).apply(
            must_take, axis=1
        )

        def one_of(class_options: list[str]):
            c = self._class_vars.get_courses_variables(class_options).sum().sum() >= 1
            self.model.add(c)

        for option in self.instance.one_of:
            one_of(option)

        def apply_pre_requisite(
            course, prerequisite_options
        ) -> list[cp_model.BoolVarT]:
            course_taken = self._class_vars.get_course_taken(course)
            course_taken_in = self._class_vars.get_course_taken_in(course)

            met_prerequisite_options_variables = []
            for i, prerequisite_option in enumerate(prerequisite_options):
                prerequisites_taken_in = [
                    self._class_vars.get_course_taken_in(course_code)
                    for course_code in prerequisite_option
                ]

                prerequisites_taken_before_class = []
                # these are more dependant variables maybe they should be kept around for use in future?
                for prereq_name, prereq_taken_in in zip(
                    prerequisite_option, prerequisites_taken_in
                ):
                    prereq_taken = self._class_vars.get_course_taken(prereq_name)
                    took_prereq_before_class = self.model.new_bool_var(
                        f"took_{prereq_taken_in}_before_{course}?"
                    )
                    self.model.add(prereq_taken_in < course_taken_in).only_enforce_if(
                        took_prereq_before_class
                    )
                    self.model.add(prereq_taken_in >= course_taken_in).only_enforce_if(
                        ~took_prereq_before_class
                    )
                    self.model.add(prereq_taken_in != 0).only_enforce_if(
                        took_prereq_before_class
                    )
                    print(prereq_taken)

                    prerequisites_taken_before_class.append(took_prereq_before_class)

                met_prereq_option = self.model.new_bool_var(
                    f"met_prereq_option_{i}_{prerequisite_option}"
                )

                # took all before class for this option
                self.model.add(
                    sum(prerequisites_taken_before_class)
                    == len(prerequisites_taken_before_class)
                ).only_enforce_if(met_prereq_option)

                self.model.add(
                    sum(prerequisites_taken_before_class)
                    != len(prerequisites_taken_before_class)
                ).only_enforce_if(~met_prereq_option)

                met_prerequisite_options_variables.append(met_prereq_option)

            # one option must be met
            self.model.add_bool_or(met_prerequisite_options_variables).only_enforce_if(
                course_taken
            )
            return met_prerequisite_options_variables

        # TODO: loop over all and do this
        self.tmp = apply_pre_requisite("PHY1020U", prerequisites["PHY1020U"])
        self.tmp = apply_pre_requisite("CSCI3090U", prerequisites["CSCI3090U"])
        self.tmp = apply_pre_requisite("CSCI2010U", prerequisites["CSCI2010U"])

    def _build_model(self):
        self._add_constraints()
        # add objective?

    def solve(self) -> GraduationRequirementsSolution:
        self.solver.parameters.max_time_in_seconds = self.config.time_limit
        self.solver.parameters.relative_gap_limit = self.config.opt_tol
        self.solver.parameters.log_search_progress = self.config.log_search_progress

        status = self.solver.solve(self.model)
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:

            for v in self._class_vars.taken_in:
                value = self.solver.value(v)
                if value != 0:
                    print(v, value)

            for v in self.tmp:
                value = self.solver.value(v)
                print(v, value)

            return GraduationRequirementsSolution(taken_courses=("no", 1))
        else:
            print("No Solution")

    def take_class(self, class_name: str):
        self.model.add(self._class_vars.get_course_taken(class_name) == 1)
