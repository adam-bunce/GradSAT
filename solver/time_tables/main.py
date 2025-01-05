from scraper.models import ListOfMinimumClassInfo
from solver.time_tables.model import (
    TTProblemInstance,
    TTSolver,
    TTFilterConstraint,
)


def read_data(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


if __name__ == "__main__":
    course_list = read_data("data.json")

    unique_courses = set()
    for course in course_list.lomci:
        unique_courses.add(course.class_code)
    # enumerate all should find 2 possible schdules with  just csci4060u but it doesnt!
    problem_instance = TTProblemInstance(
        courses=course_list.lomci,
        forced_conflicts=[],
        filter_constraints=[
            TTFilterConstraint(course_codes=["CSCI4060U"], eq=1),
            # TTFilterConstraint(course_codes=["CSCI1060U"], eq=1),
        ],
    )

    # problem_instance.add_forced_conflict(start=0, end=2359, day="wednesday")
    # problem_instance.add_forced_conflict(start=0, end=2359, day="friday")

    solver = TTSolver(problem_instance=problem_instance, enumerate_all_solutions=True)

    solution = solver.solve()
    print(solution)
