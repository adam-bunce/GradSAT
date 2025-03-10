import asyncio
from typing import Optional
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from grad_sat.cp_sat.time_tables.main import generate_multiple_optimal_schedules
from grad_sat.cp_sat.time_tables.model import (
    TTFilterConstraint,
    TTProblemInstance,
    TTSolver,
    ForcedConflict,
    OptimizationTarget,
)
from grad_sat.scraper.models import ListOfMinimumClassInfo

router = APIRouter()

def read_data(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


course_list = read_data("grad_sat/cp_sat/time_tables/data.json")

class TimeTableRequest(BaseModel):
    forced_conflicts: list[ForcedConflict]
    filter_constraints: list[TTFilterConstraint]
    optimization_target: OptimizationTarget
    enumerate_all: Optional[bool] = None


@router.post("/time-table")
def generate_time_tables(ttr: TimeTableRequest):
    print(ttr)

    problem_instance = TTProblemInstance(
        courses=course_list.lomci,
        forced_conflicts=ttr.forced_conflicts,
        filter_constraints=ttr.filter_constraints,
        optimization_target=ttr.optimization_target,
    )

    solver = TTSolver(problem_instance=problem_instance)

    solution = solver.solve()
    return solution.response()


@router.post("/all-time-tables")
def generate_all_time_tables(ttr: TimeTableRequest):
    async def time_table_generator():
        problem_instance = TTProblemInstance(
            courses=course_list.lomci,
            forced_conflicts=ttr.forced_conflicts,
            filter_constraints=ttr.filter_constraints,
            optimization_target=ttr.optimization_target,
        )

        for sol in generate_multiple_optimal_schedules(problem_instance):
            await asyncio.sleep(0.01)  # sends as 1 if no sleep?
            yield f"event:scheduleEvent\ndata: {sol.response().model_dump_json()}\n\n"

    return StreamingResponse(time_table_generator(), media_type="text/event-stream")
