import asyncio
import json
import os
import re
from collections import defaultdict
from enum import Enum
from typing import Optional, Tuple, List, Literal

from fastapi.responses import StreamingResponse
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
import pymupdf

from grad_sat.cp_sat.v2.dependent_variables import false_var
from grad_sat.cp_sat.v2.model import GraduationRequirementsInstance, GraduationRequirementsConfig, \
    GraduationRequirementsSolver, CourseType
from grad_sat.scraper.models import ListOfMinimumClassInfo
from grad_sat.cp_sat.v2.feasability_model import get_cs_program_map_feas, \
    GraduationRequirementsInstanceFeas, GraduationRequirementsFeasabilitySolver, SolverFeedback, ProgramMapFeas
from grad_sat.cp_sat.time_tables.main import generate_multiple_optimal_schedules
from grad_sat.cp_sat.time_tables.model import (
    TTFilterConstraint,
    TTProblemInstance,
    TTSolver,
    ForcedConflict,
    OptimizationTarget,
)

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("UI_URL")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TimeTableRequest(BaseModel):
    forced_conflicts: list[ForcedConflict]
    filter_constraints: list[TTFilterConstraint]
    optimization_target: OptimizationTarget
    enumerate_all: Optional[bool] = None


def read_data(path: str) -> ListOfMinimumClassInfo:
    with open(path, "r") as f:
        tmp = f.read()
        return ListOfMinimumClassInfo.model_validate_json(tmp)


course_list = read_data("grad_sat/cp_sat/time_tables/data.json")


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


class CourseSelection(BaseModel):
    course_name: str
    course_type: int
    semester: int


@app.post("/process-pdf")
def process_pdf(file: UploadFile = File(...)):
    print(file.size)
    doc = pymupdf.open(stream=file.file.read())
    all_matches = []
    for page in doc:
        all_matches.extend(
            [
                course.replace("\n", "")
                for course in re.findall("[A-Z]{3,4}[ \r\n]*[0-9]{4}U", page.get_text())
                # NOTE(adam): added spce to [\r\n] for my custom test format
            ]
        )

    res: list[CourseSelection] = []
    for semester, semester_courses in enumerate([all_matches[i:i + 5] for i in range(0, len(all_matches), 5)]):
        for semester_course in semester_courses:
            res.append(CourseSelection(
                course_name=semester_course.replace(" ", ""),
                semester=semester,
                course_type=1,  # TODO; this is hardcoded as taken
            ))

    return res


class PlannedCourseType(Enum):
    UNKNOWN = 0
    USER_COMPLETED = 1
    USER_DESIRED = 2
    SOLVER_PLANNED = 3


class PlannedCourse(BaseModel):
    course_name: str
    semester: int
    course_type: PlannedCourseType


class GeneratePlanRequest(BaseModel):
    completed_courses: list[tuple[str, int]]
    taken_in: list[tuple[str, int]]
    course_map: Literal["computer-science"]
    semester_layout: dict[str, int]  # semester name -> # of courses person wants to take
    course_ratings: list[tuple[str, int]]
    must_take: list[str]
    must_not_take: list[str]


class GeneratePlanResponse(BaseModel):
    # during render on ui side always sort to maintain order within semesters
    courses: list[PlannedCourse]
    issues: list[SolverFeedback]


course_maps: dict[str, ProgramMapFeas] = {
    "computer-science": get_cs_program_map_feas()
}


@app.post("/planner-generate")
def verify_graduation_requirements(genPlanReq: GeneratePlanRequest) -> GeneratePlanResponse:
    print("enter planner generate")
    sem_counts = defaultdict(int)
    for course, sem in genPlanReq.taken_in:
        sem_counts[sem] += 1

    for sem, count in sem_counts.items():
        print("Sem:", sem, "count", count)

    course_names = [course for course, _ in genPlanReq.taken_in]
    if len(course_names) != len(set(course_names)):
        res = GeneratePlanResponse(courses=[], issues=[])
        for course in [s for s in set(course_names) if course_names.count(s) > 1]:
            res.issues.append(SolverFeedback(category="Course Repeated",
                                             reason=f"Attempt to {course} take {course_names.count(course)} times",
                                             variable=False))

        return res

    gr_instance = GraduationRequirementsInstance(
        program_map=course_maps[genPlanReq.course_map],
        semesters=list(genPlanReq.semester_layout.keys()),
        pickle_path="grad_sat/cp_sat/v2/uoit_courses_copy.pickle",
    )
    gr_config = GraduationRequirementsConfig(print_stats=False)

    solver = GraduationRequirementsSolver(
        problem_instance=gr_instance,
        config=gr_config,
    )

    for course, semesterInt in genPlanReq.completed_courses:
        solver.take_class_in(course, semesterInt)

    for course, semesterInt in genPlanReq.taken_in:
        solver.take_class_in(course, semesterInt)

    for course in genPlanReq.must_take:
        solver.take_class(course)

    for course in genPlanReq.must_not_take:
        solver.dont_take_class(course)

    solver.set_star_rating_maximization_target(genPlanReq.course_ratings)

    res = GeneratePlanResponse(courses=[], issues=[])
    try:
        solution = solver.solve()
    except Exception as e:
        print("error solving generation model")
        raise HTTPException(status_code=500, detail=str(e))

    if len(solution.taken_courses) == 0:
        gr_feas_instance = GraduationRequirementsInstanceFeas(
            program_map=get_cs_program_map_feas(),
            semesters=list(genPlanReq.semester_layout.keys()),
            pickle_path="grad_sat/cp_sat/v2/uoit_courses_copy.pickle"
        )

        # failed to solve
        feas_solver = GraduationRequirementsFeasabilitySolver(
            problem_instance=gr_feas_instance,
            config=GraduationRequirementsConfig(print_stats=False),
            completed_classes=[course for course, _ in genPlanReq.completed_courses] + [course for course, _ in
                                                                                        genPlanReq.taken_in],
            must_take=genPlanReq.must_take,
            must_not_take=genPlanReq.must_not_take
        )

        for course, semesterInt in genPlanReq.taken_in:
            feas_solver.take_class_in(course, semesterInt)

        for course in genPlanReq.must_take:
            feas_solver.take_class(course)

        for course in genPlanReq.must_not_take:
            feas_solver.dont_take_class(course)

        try:
            res.issues = feas_solver.solve()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

        # res.issues.append("Failed to find solution")

    for semester, courses in solution.taken_courses.items():
        for course in courses:
            course = course[:-4]  # trim _(T)'s
            course_type = PlannedCourseType.UNKNOWN
            if course.upper() in [course_name for course_name, _ in genPlanReq.completed_courses]:
                course_type = PlannedCourseType.USER_COMPLETED
            elif course.upper() in [course_name for course_name, _ in genPlanReq.taken_in]:
                course_type = PlannedCourseType.USER_DESIRED
            else:
                course_type = PlannedCourseType.SOLVER_PLANNED

            res.courses.append(PlannedCourse(course_name=course,
                                             semester=semester,
                                             course_type=course_type))

    return res


class VerifyPlanRequest(BaseModel):
    completed_courses: list[tuple[str, int]]
    taken_in: list[tuple[str, int]]
    course_map: Literal["computer-science"]
    semester_layout: dict[str, int]
    must_take: list[str]
    must_not_take: list[str]

class VerifyPlanResponse(BaseModel):
    issues: list[SolverFeedback]


@app.post("/graduation-verification")
def verify_graduation_requirements(verifyReq: VerifyPlanRequest) -> VerifyPlanResponse:
    course_names = [course for course, _ in verifyReq.taken_in]
    if len(course_names) != len(set(course_names)):
        res = GeneratePlanResponse(courses=[], issues=[])
        for course in [s for s in set(course_names) if course_names.count(s) > 1]:
            res.issues.append(SolverFeedback(category="Course Repeated",
                                             reason=f"Attempt to {course} take {course_names.count(course)} times",
                                             variable=False))

        return res
    res = VerifyPlanResponse(issues=[])
    try:
        feedback = verify_grad_req(verifyReq.taken_in, verifyReq.semester_layout, verifyReq.completed_courses, verifyReq.must_take, verifyReq.must_not_take)
        res.issues = feedback
        return res
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def verify_grad_req(taken_in: list[tuple[str, int]], semester_layout: dict[str, int],
                    completed_courses: list[tuple[str, int]], must_take: list[str], must_not_take: list[str]) -> list[SolverFeedback]:
    gr_feas_instance = GraduationRequirementsInstanceFeas(
        program_map=get_cs_program_map_feas(),
        semesters=list(semester_layout.keys()),
        pickle_path="grad_sat/cp_sat/v2/uoit_courses_copy.pickle"
    )

    feas_solver = GraduationRequirementsFeasabilitySolver(
        problem_instance=gr_feas_instance,
        config=GraduationRequirementsConfig(print_stats=False),
        completed_classes=[course for course, _ in completed_courses] + [course for course, _ in taken_in],
        must_not_take=must_not_take,
        must_take=must_take

    )

    for course, semesterInt in taken_in:
        feas_solver.take_class_in(course, semesterInt)

    # NOTE: this is only used in generation i think.
    # for course in must_take:
    #     feas_solver.take_class(course)
    #
    # for course in must_not_take:
    #     feas_solver.dont_take_class(course)

    feedback_list = feas_solver.solve()
    return feedback_list


@app.get("/health")
def health():
    return "OK"
