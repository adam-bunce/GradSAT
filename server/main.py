import asyncio
import json
from time import sleep
from typing import Optional
from fastapi.responses import StreamingResponse

from fastapi import FastAPI
from pydantic import BaseModel

from scraper.models import ListOfMinimumClassInfo
from solver.time_tables.model import (
    TTFilterConstraint,
    TTProblemInstance,
    TTSolver,
    ForcedConflict,
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TimeTableRequest(BaseModel):
    forced_conflicts: list[ForcedConflict]
    filter_constraints: list[TTFilterConstraint]
    enumerate_all: Optional[bool] = None


def read_data(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


course_list = read_data("solver/time_tables/data.json")

tmp = """{"forced_conflicts":[{"day":"MONDAY","start":115,"stop":2345}],"filter_constraints":[]}"""
print(TimeTableRequest.parse_raw(tmp))


@app.post("/time-table")
def generate_time_tables(ttr: TimeTableRequest):
    print(ttr)

    problem_instance = TTProblemInstance(
        courses=course_list.lomci,
        forced_conflicts=ttr.forced_conflicts,
        filter_constraints=ttr.filter_constraints,
    )

    solver = TTSolver(problem_instance=problem_instance)

    solution = solver.solve()
    return solution.response()


@app.post("/all-time-tables")
def generate_all_time_tables(ttr: TimeTableRequest):
    async def time_table_generator():
        res = [1, 2, 3, 4, 5]
        for num in res:
            data = json.dumps({"data": num})

            # erhmm
            await asyncio.sleep(1)
            yield f"event: scheduleEvent\ndata:{json.dumps({'data': num})}\n\n"

    return StreamingResponse(time_table_generator(), media_type="text/event-stream")
