from fastapi import FastAPI
from pydantic import BaseModel

from scraper.models import MinimumClassInfo, ListOfMinimumClassInfo
from solver.time_tables.model import TTFilterConstraint, TTProblemInstance, TTSolver

app = FastAPI()


class TimeTableRequest(BaseModel):
    forced_conflicts: list[tuple[int, int, str]]
    filter_constraints: list[TTFilterConstraint]


def read_data(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


course_list = read_data("solver/time_tables/data.json")


@app.post("/time_table")
def generate_time_tables(ttr: TimeTableRequest):

    problem_instance = TTProblemInstance(
        courses=course_list.lomci,
        forced_conflicts=ttr.forced_conflicts,
        filter_constraints=ttr.filter_constraints,
    )

    solver = TTSolver(problem_instance=problem_instance)

    solution = solver.solve()
    return solution.response()
