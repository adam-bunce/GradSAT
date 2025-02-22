import json
from typing import Generator

from sqlalchemy import select

from scout_platform.db.schema import Course
from scout_platform.scraper.info_reducer import raw_to_minimum
from scout_platform.scraper.models import ListOfMinimumClassInfo, MinimumClassInfo
from scout_platform.cp_sat.time_tables.model import (
    TTProblemInstance,
    TTSolver,
    TTFilterConstraint,
    OptimizationTarget,
    TTSolution,
)

from scout_platform.db.database import get_db, create_url


def read_data_from_db() -> ListOfMinimumClassInfo:
    all_data: list[MinimumClassInfo] = []
    with get_db(create_url()) as db:
        query = select(Course.data)
        courses = db.execute(query).fetchall()
        for crs in courses:
            mci = raw_to_minimum(crs[0])  # return type is a tuple w/ data as only col
            all_data.append(mci)

    lomci = ListOfMinimumClassInfo(lomci=all_data)
    with open("tmp.json", "w") as f:
        json.dump(lomci.model_dump(), f, indent=4)

    return lomci


def read_data_from_disk(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


# recursive impl where i exclude 1 course, then 2, then 3... would be better i think
def generate_multiple_optimal_schedules(
        problem_instance: TTProblemInstance,
) -> Generator[TTSolution, None, None]:
    already_excluded_courses: set[str] = set()
    courses_to_exclude: set[str] = set()
    solutions_count: int = 0
    seen_solutions: dict[str, bool] = dict()  # sorted list of all crn's in schedule

    # initial solve
    solver = TTSolver(problem_instance=problem_instance)
    solution = solver.solve()

    # would i get duplicate solutions? idk (Adam Later: yes)
    if solution.status_ok:
        solutions_count += 1
        solution_str = "_".join(sorted(solution.courses_taken))
        print(solution_str)
        seen_solutions[solution_str] = True
        yield solution

        new_courses = set(solution.courses_taken) - already_excluded_courses
        courses_to_exclude = courses_to_exclude.union(new_courses)

        while courses_to_exclude and solutions_count < 10:
            print("seen solutions:", seen_solutions)
            # solve again without that course being allowed
            course_to_exclude = courses_to_exclude.pop()
            print(f"excluding {course_to_exclude}")
            solver = TTSolver(problem_instance=problem_instance)
            solver.exclude_course(course_to_exclude)
            solution = solver.solve()

            if solution.status_ok:
                solution_str = "_".join(sorted(solution.courses_taken))
                print(solution_str)
                if solution_str in seen_solutions:
                    continue
                else:
                    seen_solutions[solution_str] = True
                    solutions_count += 1
                    yield solution
                    new_courses = set(solution.courses_taken) - already_excluded_courses
                    courses_to_exclude = courses_to_exclude.union(new_courses)
            else:
                print(f"failed to generate schedule without {course_to_exclude}")
    else:
        # no solutions
        yield solution


if __name__ == "__main__":
    course_list = read_data_from_disk("../reduced_info.json")
    # course_list = read_data_from_db()
    print(course_list.lomci[:5])

    course_list = read_data_from_disk("data.json")

    problem_instance = TTProblemInstance(
        courses=course_list.lomci,
        forced_conflicts=[],
        filter_constraints=[
            TTFilterConstraint(course_codes=["CSCI4060U", "PHY3900U"], eq=2),
            # TTFilterConstraint(course_codes=["CSCI1060U"], eq=1),
        ],
        optimization_target=OptimizationTarget.TimeOnCampus,
    )

    for sol in generate_multiple_optimal_schedules(problem_instance):
        print(sol)
        print("------------------------")

    exit(1)

    unique_courses = set()
    for course in course_list.lomci:
        unique_courses.add(course.class_code)

    solutions = []
    # enumerate all should find 2 possible schdules with  just csci4060u but it doesnt!
    problem_instance = TTProblemInstance(
        courses=course_list.lomci,
        forced_conflicts=[],
        filter_constraints=[
            TTFilterConstraint(course_codes=["CSCI4060U", "PHY3900U"], eq=2),
            # TTFilterConstraint(course_codes=["CSCI1060U"], eq=1),
        ],
        optimization_target=OptimizationTarget.CoursesTaken,
    )

    solver = TTSolver(problem_instance=problem_instance)
    solution = solver.solve()
    if solution.status_ok:
        solutions.append(solution)

    # try to exclude all courses that were taken to generate more possibilities on following solves (1 layer deep)
    for course in solution.courses_taken:
        problem_instance = TTProblemInstance(
            courses=course_list.lomci,
            forced_conflicts=[],
            filter_constraints=[
                TTFilterConstraint(course_codes=["CSCI4060U", "PHY3900U"], eq=2),
                # TTFilterConstraint(course_codes=["CSCI1060U"], eq=1),
            ],
            optimization_target=OptimizationTarget.CoursesTaken,
        )

        solver = TTSolver(problem_instance=problem_instance)
        solver.exclude_course(course)
        solution = solver.solve()

        if solution.status_ok:
            solutions.append(solution)

    for solution in solutions:
        print(solution)
