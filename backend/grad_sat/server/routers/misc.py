from fastapi import File, UploadFile, APIRouter
from pydantic import BaseModel
from pymupdf import pymupdf
import re

router = APIRouter()

class CourseSelection(BaseModel):
    course_name: str
    course_type: int
    semester: int

@router.post("/process-pdf")
def process_pdf(file: UploadFile = File(...)):
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


@router.get("/health")
def health():
    return "OK"
