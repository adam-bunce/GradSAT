import csv
from collections import defaultdict

from solver.v2.parser.dnf_convertor import expr_to_dnf
from solver.v2.static import Programs

from pydantic import (
    BaseModel,
    Field,
    constr,
    NonNegativeFloat, )


class Course(BaseModel):
    year_level: int = Field(description="the year level of the course; 1,2,3,4")
    program: Programs = Field(description="program the course is part of")
    course_prefix: constr(min_length=3, max_length=4)
    course_code: constr(min_length=5, max_length=5)
    course_name: str
    description: str

    credit_hours: NonNegativeFloat
    lecture_hours: NonNegativeFloat
    laboratory_hours: NonNegativeFloat
    tutorial_hours: NonNegativeFloat
    other_hours: NonNegativeFloat

    notes: str
    experiential_learning: bool
    recommended: str

    # DNF list (1030 and 1050) or 1060 -> [[1030, 1050], [1060]]
    credit_restrictions: list[list[str]]
    pre_requisites: list[list[str]]
    post_requisites: list[list[str]]
    pre_requisites_with_concurrency: list[list[str]]
    co_requisites: list[list[str]]
    credit_restrictions: list[list[str]]
    cross_listed: list[list[str]]

    def __str__(self) -> str:
        return f"{self.course_name} ({self.course_prefix}{str(self.course_code)})"


class CourseCsvParser:
    def __init__(self, path: str):
        self.path = path
        self.curr_row = 0
        self.failed_hours: dict[str, list[int]] = defaultdict(list)
        self.failed_exprs: dict[str, list[int]] = defaultdict(list)

    def parse(self, show_errors: bool = False) -> list[Course]:
        courses = []
        with open(self.path, "r") as csv_file:
            reader = csv.reader(csv_file)

            for i, row in enumerate(reader):
                self.curr_row = i
                if i == 0:
                    continue
                try:
                    courses.append(self.__parse_row(row))
                except Exception as e:
                    print(f"failed to parse line {i} into course, err: {e}")

        if show_errors:
            print("Failed Hour Parses:")
            for pos, val in self.failed_hours.items():
                print(pos, val)

            print("Failed Expr Parses:")
            for pos, val in self.failed_exprs.items():
                print(pos, val)

        return courses

    def __parse_row(self, row: list[str]) -> Course:
        return Course(
            year_level=self.__course_level(row[2]),
            course_prefix=row[1],
            course_code=row[2],
            course_name=row[3],
            program=row[4],
            description=row[5],
            credit_hours=self.__parse_hrs(row[6]),
            lecture_hours=self.__parse_hrs(row[7]),
            tutorial_hours=self.__parse_hrs(row[8]),
            notes=row[9],
            credit_restrictions=self.__parse_expr(row[10]),
            pre_requisites=self.__parse_expr(row[11]),
            post_requisites=[],  # thesis combo
            laboratory_hours=self.__parse_hrs(row[12]),
            experiential_learning=self.__parse_truthy(row[13]),
            recommended=row[14],
            cross_listed=self.__parse_expr(row[15]),
            other_hours=self.__parse_hrs(row[16]),
            pre_requisites_with_concurrency=self.__parse_expr(row[17]),
            co_requisites=self.__parse_expr(row[18]),
        )

    def __parse_expr(self, expr: str) -> list[list[str]]:
        if not expr:
            return []

        expr = expr.replace(",", "and")
        try:
            dnf = expr_to_dnf(expr)
            return [[course.replace(" ", "") for course in term] for term in dnf]
        except Exception as e:
            self.failed_exprs[expr].append(self.curr_row)
        return []

    def __parse_hrs(self, hours: str) -> float:
        try:
            return float(hours)
        except ValueError:
            if hours not in [None, "", " "]:
                self.failed_hours[hours].append(self.curr_row)
        return 0.0

    @staticmethod
    def __parse_truthy(value: str) -> bool:
        if value.lower() in ["yes", "ok"]:
            return True
        return False

    @staticmethod
    def __course_level(course: str) -> int:
        buf = ""
        for c in course:
            if c.isnumeric():
                buf += c

        if buf == "":
            return -1

        res = int(buf[0])
        if res > 4:
            return 4

        return res


if __name__ == "__main__":
    p = CourseCsvParser(path="../../../misc/uoit_courses.csv")
    p.parse(show_errors=True)
