import asyncio
import json
import re
from time import sleep
from typing import Optional

import pandas as pd
from fastapi.responses import StreamingResponse
from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel
import pymupdf

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


class VerifyGradRequirementsRequest(BaseModel):
    completed_courses: list[str]


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


tmp = '{"completed_courses":["ACST1000U"," ACST7000U"," BUSI1020U"," COMM1050U"," CSCI1030U"," CSCI1060U"," CSCI1061U"," CSCI2000U"," CSCI2010U"," CSCI2020U"," CSCI2040U"," CSCI2050U"," CSCI2072U"," CSCI2110U"," CSCI2160U"," CSCI3030U"," CSCI3055U"," CSCI3070U"," CSCI3090U"," CSCI3230U"," CSCI3310U"," CSCI4020U"," CSCI4030U"," CSCI4040U"," CSCI4050U"," CSCI4060U"," CSCI4410U"," CSCI4420U"," ENVS1000U"," INFR1016U"," INFR1100U"," MATH1010U"," MATH1020U"," MATH1020U"," MATH2050U"," MATH2050U"," MATH3090U"," PHY1010U"," PHY1020U"," PHY2900U"," PHY3900U"," SOCI1000U"," STAT2010U"]}'
print("vfrr:", VerifyGradRequirementsRequest.parse_raw(tmp))


@app.post("/graduation-verification")
def verify_graduation_requirements(vgrr: VerifyGradRequirementsRequest):
    if len(vgrr.completed_courses) > 5:
        return {"can_graduate": True}
    else:
        return {"can_graduate": False}
