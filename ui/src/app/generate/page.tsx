"use client";

import { useEffect, useState } from "react";
import WindowSelect from "@/components/window-select";
import { Button } from "@/components/ui/button";
import generateTimeTable, {
  DayOfTheWeek,
  ForcedConflict,
  FilterConstraint,
  GenerateTimeTableResponse,
} from "@/api/generateTimeTable";
import STFilterConstraint from "@/components/filter-constraint";
import WeeklySchedule from "@/components/weekly-schedule";

// having like text on the right size that is synopsis of the constraint and also modifieable (remove things)
// would be nice // also ~need~ calendar summary of forced conflicts
// TODO: plug it in and get api connected
const temp_schedule = {
  wednesday: [
    {
      crn: 72845,
      name: "CSCI1060U",
      meeting_type: "Lecture",
      start_time: 810,
      end_time: 930,
    },
    {
      crn: 72677,
      name: "MATH2050U",
      meeting_type: "Lecture",
      start_time: 1840,
      end_time: 2000,
    },
  ],
  friday: [
    {
      crn: 72845,
      name: "CSCI1060U",
      meeting_type: "Lecture",
      start_time: 810,
      end_time: 930,
    },
  ],
  tuesday: [
    {
      crn: 72848,
      name: "CSCI1060U",
      meeting_type: "Laboratory",
      start_time: 1240,
      end_time: 1530,
    },
  ],
  monday: [
    {
      crn: 72677,
      name: "MATH2050U",
      meeting_type: "Lecture",
      start_time: 1840,
      end_time: 2000,
    },
  ],
  thursday: [
    {
      crn: 73012,
      name: "MATH2050U",
      meeting_type: "Tutorial",
      start_time: 1410,
      end_time: 1530,
    },
  ],
};

function Page() {
  const [filterConstraints, setFilterConstraints] = useState<
    FilterConstraint[]
  >([]);
  const [forcedConflicts, setForcedConflicts] = useState<ForcedConflict[]>([]);
  const [schedule, setSchedule] = useState<null | GenerateTimeTableResponse>({
    ...temp_schedule,
  });
  const [scheduleIsLoading, setScheduleIsLoading] = useState(false);

  const genSchedule = async () => {
    setScheduleIsLoading(true);

    try {
      const dayToCourseList = await generateTimeTable(
        filterConstraints,
        forcedConflicts,
      );
      setSchedule(dayToCourseList);
    } finally {
      setScheduleIsLoading(false);
    }
  };

  const updateFilterConstraints = (
    uuid: string,
    updateType: string,
    newValue: any,
  ) => {
    const record = filterConstraints.find((fc) => fc.uuid === uuid);
    if (!record) return;
    let newRecord = { ...record, [updateType]: newValue };
    setFilterConstraints(
      filterConstraints.map((constraint) =>
        constraint.uuid === uuid ? newRecord : constraint,
      ),
    );
  };

  const updateForcedConflict = (
    uuid: string,
    updateType: string,
    newValue: number | DayOfTheWeek,
  ) => {
    const record = forcedConflicts.find((fc) => fc.uuid === uuid);
    if (!record) return;
    let newRecord = { ...record, [updateType]: newValue };

    setForcedConflicts(
      forcedConflicts.map((conflict) =>
        conflict.uuid == uuid ? newRecord : conflict,
      ),
    );
  };

  const deleteForcedConflict = (uuid: string) => {
    setForcedConflicts(forcedConflicts.filter((fc) => fc.uuid !== uuid));
  };

  return (
    <div className={"space-y-3"}>
      {/*NOTE: events work fine but the model can't get multiple optimal solutions w/o me modifying it */}
      {/*<Button*/}
      {/*  onClick={() =>*/}
      {/*    getEvents(filterConstraints, forcedConflicts, (ev) => console.log(ev))*/}
      {/*  }*/}
      {/*>*/}
      {/*test events*/}
      {/*</Button>*/}

      <div className={"flex flex-col  gap-4"}>
        <div className={"border border-black space-y-2 bg-white "}>
          <h2
            className={
              "text-lg p-3 font-semibold border-b border-b-gray-400 flex flex-row justify-between"
            }
          >
            Forced Conflicts
            <Button
              variant="outline"
              onClick={() => {
                setForcedConflicts([
                  ...forcedConflicts,
                  {
                    uuid: crypto.randomUUID(),
                  },
                ]);
              }}
            >
              +
            </Button>
          </h2>

          <div className={"p-3 space-y-2"}>
            {forcedConflicts.map((conflict, idx) => (
              <div
                className={
                  "sm:flex sm:flex-row md:space-x-2 space-y-2 sm:space-y-0 justify-between align-bottom"
                }
                key={conflict.uuid}
              >
                <WindowSelect
                  uuid={conflict.uuid}
                  startTime={conflict.start}
                  stopTime={conflict.stop}
                  dayOfTheWeek={conflict.day}
                  onChange={updateForcedConflict}
                />
                <div className={"flex flex-row justify-end"}>
                  <Button
                    variant="destructive"
                    onClick={() => deleteForcedConflict(conflict.uuid)}
                  >
                    -
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={"border border-black bg-white "}>
          <h2
            className={
              "font-semibold text-lg p-3 border-b border-b-gray-400 flex flex-row justify-between items-center"
            }
          >
            Filter Constraints
            <Button
              variant="outline"
              onClick={() => {
                setFilterConstraints([
                  ...filterConstraints,
                  {
                    uuid: crypto.randomUUID(),
                    course_codes: [],
                    subjects: [],
                    year_levels: [],
                  },
                ]);
              }}
            >
              +
            </Button>
          </h2>
          <div className={"p-3"}>
            {filterConstraints.map((fc) => (
              <div
                key={fc.uuid}
                className={
                  "last:pb-0 last:border-0 border-b pb-2 pt-2  border-dashed border-gray-500"
                }
              >
                {/* TODO: accordion & hide after new one is created*/}
                <STFilterConstraint
                  uuid={fc.uuid}
                  course_codes={fc.course_codes}
                  subjects={fc.subjects}
                  year_levels={fc.year_levels}
                  onChange={updateFilterConstraints}
                />
                <div className={"flex flex-row justify-end"}>
                  <Button
                    variant="destructive"
                    onClick={() =>
                      setFilterConstraints(
                        filterConstraints.filter(
                          (inclFc) => inclFc.uuid !== fc.uuid,
                        ),
                      )
                    }
                  >
                    -
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <Button onClick={() => genSchedule()}>GENERATE</Button>

      {/* TODO schedule component */}
      <div>
        {!scheduleIsLoading && schedule !== null && (
          <WeeklySchedule courses={schedule} />
        )}
        {/*TODO: elapsed time would be nice lowk*/}
        {scheduleIsLoading && (
          <div
            className={
              "h-[100px] w-[80%] m-auto bg-gray-400 animate-pulse mt-8 flex items-center justify-center"
            }
          >
            Generating Schedule
          </div>
        )}
      </div>
    </div>
  );
}

export default Page;
