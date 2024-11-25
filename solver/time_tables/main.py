from scraper.models import ListOfMinimumClassInfo
from solver.time_tables.model import TTProblemInstance, TTSolver


def read_data(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


if __name__ == "__main__":
    course_list = read_data("data.json")

    problem_instance = TTProblemInstance(courses=course_list.lomci, forced_conflicts=[])

    problem_instance.add_forced_conflict(start=0, end=1300, day="monday")
    problem_instance.add_forced_conflict(start=1300, end=2359, day="friday")

    solver = TTSolver(problem_instance=problem_instance)

    solution = solver.solve()
    print(solution)
