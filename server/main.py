import asyncio
import json
import re
from typing import Optional

from fastapi.responses import StreamingResponse
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import pymupdf

from scraper.models import ListOfMinimumClassInfo
from solver.time_tables.main import generate_multiple_optimal_schedules
from solver.time_tables.model import (
    TTFilterConstraint,
    TTProblemInstance,
    TTSolver,
    ForcedConflict,
    OptimizationTarget,
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
    optimization_target: OptimizationTarget
    enumerate_all: Optional[bool] = None


class VerifyGradRequirementsRequest(BaseModel):
    completed_courses: list[str]


def read_data(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


course_list = read_data("solver/time_tables/data.json")


@app.post("/time-table")
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


@app.post("/all-time-tables")
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


@app.post("/process-pdf")
def process_pdf(file: UploadFile = File(...)):
    print(file.size)
    doc = pymupdf.open(stream=file.file.read())
    all_matches = []
    for page in doc:
        all_matches.extend(
            [
                course.replace("\n", "")
                for course in re.findall("[A-Z]{3,4}[\r\n]*[0-9]{4}U", page.get_text())
            ]
        )

    return {"matches": list(sorted(all_matches))}


@app.post("/graduation-verification")
def verify_graduation_requirements(vgrr: VerifyGradRequirementsRequest):
    if len(vgrr.completed_courses) > 5:
        return {"can_graduate": True}
    else:
        return {"can_graduate": False}
