import csv

from solver.v2.model import Course, Programs


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
