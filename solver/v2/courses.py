import csv

from solver.v2.static import Programs

from pydantic import (
    BaseModel,
    Field,
    constr,
    NonNegativeFloat,
)


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

    # DNF list (1030 and 1050) or 1060 -> [[1030, 1050], [1060]]
    credit_restrictions: list[list[str]]
    pre_requisites: list[list[str]]
    post_requisites: list[list[str]]
    pre_requisites_with_concurrency: list[list[str]]
    co_requisites: list[list[str]]
    credit_restrictions: list[list[str]]

    def __str__(self) -> str:
        return f"{self.course_name} ({self.course_prefix}{str(self.course_code)})"


def c(
    lvl: int,
    prog: Programs,
    prefix: str,
    code: str,
    name: str,
    credit_hours: int,
    lecture_hours: int,
    laboratory_hours: int,
    credit_restrictions: list[list[str]],
    prerequisites: list[list[str]],
    prerequisite_with_concurrency: list[list[str]],
):
    return Course(
        year_level=lvl,
        program=prog,
        course_prefix=prefix,
        course_code=code,
        course_name=name,
        credit_restrictions=credit_restrictions,
        prerequisites=prerequisites,
        prerequisites_with_concurrency=prerequisite_with_concurrency,
    )


# parse csv into smth like this indexable by course code
# fmt:off
course_catalog: list[Course] = [
    c(1, Programs.science, "CSCI", "1030U", "Introduction to Computer Science", 3, 3, 3, [["BUSI1830U", "CSCI1020U", "CSCI1030U", "CSCI1600U"]], [], []),
    c(1, Programs.science, "CSCI", "1060U", "Programming Workshop I", 3, 3, 3, [["CSCI2030U", "INFR1100U", "ENGR1200U"]], [], []),
    c(1, Programs.science, "CSCI", "1061U", "Programming Workshop II", [], [], []),
]

# fmt:on


def parse_courses_csv(path: str):
    with open("path", newline="") as csvfile:
        csv_reader = csv.reader(csvfile, delimiter=" ")
        for row in csv_reader:
            print(row)
