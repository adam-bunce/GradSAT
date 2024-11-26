import json
import os
from typing import Dict, List

from models import (
    ClassInfoList,
    MinimumClassInfo,
    MinimumMeetingTime,
    ListOfMinimumClassInfo,
)


def process_json_files(
    base_offset: int, step: int, max_offset: int
) -> List[MinimumClassInfo]:
    all_data: list[MinimumClassInfo] = []

    for offset in range(base_offset, max_offset + step, step):
        filename = f"limit=50_offset={offset}.json"

        if os.path.exists(filename):
            with open(filename, "r") as f:
                file_contents = f.read()

                class_list: ClassInfoList = ClassInfoList.model_validate_json(
                    file_contents
                )

                for cl in class_list.class_list:
                    print(cl.linkedSections.values())
                    tmp = MinimumClassInfo(
                        id=cl.courseReferenceNumber,
                        class_code=cl.subjectCourse,
                        type=cl.scheduleTypeDescription,
                        subject=cl.subject,
                        meeting_times=[
                            MinimumMeetingTime(
                                begin_time=meeting.meetingTime.beginTime,
                                end_time=meeting.meetingTime.endTime,
                                monday=meeting.meetingTime.monday,
                                tuesday=meeting.meetingTime.tuesday,
                                wednesday=meeting.meetingTime.wednesday,
                                thursday=meeting.meetingTime.thursday,
                                friday=meeting.meetingTime.friday,
                                saturday=meeting.meetingTime.saturday,
                                sundray=meeting.meetingTime.sunday,
                            )
                            for meeting in cl.meetingsFaculty
                            if any(
                                [
                                    meeting.meetingTime.beginTime,
                                    meeting.meetingTime.endTime,
                                    meeting.meetingTime.monday,
                                    meeting.meetingTime.tuesday,
                                    meeting.meetingTime.wednesday,
                                    meeting.meetingTime.thursday,
                                    meeting.meetingTime.friday,
                                    meeting.meetingTime.saturday,
                                    meeting.meetingTime.sunday,
                                ]
                            )
                        ],
                        linked_sections=list(cl.linkedSections.values()),
                    )

                    # this isn't a meeting time (clean data here, not in model code please)
                    # {
                    #     "begin_time": null,
                    #     "end_time": null,
                    #     "monday": false,
                    #     "tuesday": false,
                    #     "wednesday": false,
                    #     "thursday": false,
                    #     "friday": false
                    # }

                    all_data.append(tmp)

            print(f"Successfully processed: {filename}")

    lomci = ListOfMinimumClassInfo(lomci=all_data)

    with open("reduced_info.json", "w") as f:
        json.dump(lomci.model_dump(), f, indent=4)

    return all_data


if __name__ == "__main__":
    results = process_json_files(base_offset=50, step=50, max_offset=10_000)

    # Print summary
    print(f"\nProcessed {len(results)} files successfully")
