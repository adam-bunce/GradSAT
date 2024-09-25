from typing import Any, List, Optional
from pydantic import BaseModel, Field


class FacultyItem(BaseModel):
    bannerId: str
    category: Any
    class_: str = Field(..., alias="class")
    courseReferenceNumber: int
    displayName: str
    emailAddress: str
    primaryIndicator: bool
    term: str


class MeetingTime(BaseModel):
    beginTime: Optional[str]
    building: Optional[str]
    buildingDescription: Optional[str]
    campus: Optional[str]
    campusDescription: Optional[str]
    category: str
    class_: str = Field(..., alias="class")
    courseReferenceNumber: int
    creditHourSession: Optional[float]
    endDate: str
    endTime: Optional[str]
    friday: bool
    hoursWeek: float
    meetingScheduleType: str
    meetingType: str
    meetingTypeDescription: str
    monday: bool
    room: Optional[str]
    saturday: bool
    startDate: str
    sunday: bool
    term: str
    thursday: bool
    tuesday: bool
    wednesday: bool


class MeetingsFacultyItem(BaseModel):
    category: str
    class_: str = Field(..., alias="class")
    courseReferenceNumber: int
    faculty: List
    meetingTime: MeetingTime
    term: str


class ClassInfo(BaseModel):
    id: int
    term: int
    termDesc: str
    courseReferenceNumber: int
    partOfTerm: str
    courseNumber: str
    subject: str
    subjectDescription: str
    sequenceNumber: str
    campusDescription: str
    scheduleTypeDescription: str
    courseTitle: str
    creditHours: int
    maximumEnrollment: int
    enrollment: int
    seatsAvailable: int
    waitCapacity: int
    waitCount: int
    waitAvailable: int
    crossList: Optional[str]
    crossListCapacity: Optional[int]
    crossListCount: Optional[int]
    crossListAvailable: Optional[int]
    creditHourHigh: Optional[int]
    creditHourLow: int
    creditHourIndicator: Optional[str]
    openSection: bool
    linkIdentifier: Optional[str]
    isSectionLinked: bool
    subjectCourse: str
    faculty: List[FacultyItem]
    meetingsFaculty: List[MeetingsFacultyItem]
    reservedSeatSummary: Any
    sectionAttributes: Any
    instructionalMethod: str
    instructionalMethodDescription: str

    # added through additional requests
    restrictions: dict[str, list[str]]
    prerequisites: str
    linkedSections: Optional[dict[str, list[int]]] = Field(default=dict())
    corequisites: str


class Model(BaseModel):
    success: bool
    totalCount: int
    data: List[ClassInfo]
    pageOffset: int
    pageMaxSize: int
    sectionsFetchedCount: int
    pathMode: str
    searchResultsConfigs: Any
    ztcEncodedImage: Any


class ClassInfoList(BaseModel):
    class_list: List[ClassInfo]
