"use client";

import { useState } from "react";
import WindowSelect from "@/components/window-select";
import { Button } from "@/components/ui/button";
import generateTimeTable, {
  DayOfTheWeek,
  ForcedConflict,
  FilterConstraint,
  CourseList,
  OptimizationTarget,
} from "@/api/generateTimeTable";
import STFilterConstraint from "@/components/filter-constraint";
import WeeklySchedule from "@/components/weekly-schedule";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useToast } from "@/hooks/use-toast";

// having like text on the right size that is synopsis of the constraint and also modifieable (remove things)
// would be nice // also ~need~ calendar summary of forced conflicts
function Page() {
  // TODO: remove test initalization
  const [filterConstraints, setFilterConstraints] = useState<
    FilterConstraint[]
  >([
    {
      course_codes: ["CSCI4060U"],
      eq: 1,
      gte: undefined,
      lte: undefined,
      uuid: crypto.randomUUID(),
      year_levels: [],
      subjects: [],
    },
  ]);
  const [forcedConflicts, setForcedConflicts] = useState<ForcedConflict[]>([]);
  const [schedule, setSchedule] = useState<null | CourseList>(null);
  const { toast } = useToast();
  const [scheduleIsLoading, setScheduleIsLoading] = useState(false);
  const [optimizationTarget, setOptimizationTarget] = useState(
    OptimizationTarget.CoursesTaken,
  );

  const genSchedule = async () => {
    setScheduleIsLoading(true);

    try {
      const dayToCourseList = await generateTimeTable(
        filterConstraints,
        forcedConflicts,
        optimizationTarget,
      );
      if (!dayToCourseList.found_solution) {
        console.log("unable to find solution");
        toast({
          title: "Error",
          description: "Unable to find solution, try relaxing constraints.",
          variant: "destructive",
        });
        return;
      }
      setSchedule(dayToCourseList.courses);
    } catch (err) {
      toast({
        title: "Error",
        description: "Unable to generate schedule",
        variant: "destructive",
      });
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
              "text-lg p-3 font-semibold border-b border-b-gray-400 flex flex-row justify-between items-center"
            }
          >
            Time Constraints
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
                  "sm:flex sm:flex-row md:space-x-2 space-y-2 sm:space-y-0 justify-between align-bottom items-center"
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
                    lte: "",
                    gte: "",
                    eq: "",
                  },
                ]);
              }}
            >
              +
            </Button>
          </h2>
          <div className={"p-3"}>
            <Accordion
              type="single"
              collapsible
              className={"w-full bg-white space-y-2"}
            >
              <>
                {filterConstraints.map((fc, idx) => (
                  <div className={"flex flex-row gap-4"} key={fc.uuid}>
                    <AccordionItem value={`item-${idx}`} className={"w-full"}>
                      <AccordionTrigger
                        className={
                          "text-md font-semibold px-2 border-black border hover:no-underline "
                        }
                      >
                        <div>
                          Constraint {idx + 1}
                          <span
                            className={
                              "text-sm font-normal text-zinc-400 px-3 no-underline"
                            }
                          >
                            <span className={"text-blue-400"}>
                              {fc.course_codes?.map((cc) => " " + cc)}{" "}
                            </span>
                            <span className={"text-red-400"}>
                              {fc.subjects?.map((cc) => " " + cc)}{" "}
                            </span>
                            <span className={"text-green-400"}>
                              {fc.year_levels?.map((cc) => " " + cc)}{" "}
                            </span>
                          </span>
                        </div>
                      </AccordionTrigger>

                      <AccordionContent
                        className={"px-2 border-black border border-t-0"}
                      >
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
                            lte={fc.lte}
                            gte={fc.gte}
                            eq={fc.eq}
                            onChange={updateFilterConstraints}
                          />
                        </div>
                      </AccordionContent>
                    </AccordionItem>

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
                ))}
              </>
            </Accordion>
          </div>
        </div>
      </div>

      <div className={"border border-black space-y-2 bg-white "}>
        <h2
          className={
            "text-lg p-3 font-semibold border-b border-b-gray-400 flex flex-row justify-between items-center"
          }
        >
          Optimization Target
        </h2>
        <div className={"p-3"}>
          <ul className={"flex flex-col sm:flex-row gap-3"}>
            <li
              className={
                "flex flex-row gap-2 hover:cursor-pointer hover:underline"
              }
              onClick={() =>
                setOptimizationTarget(OptimizationTarget.CoursesTaken)
              }
            >
              <input
                readOnly={true}
                type="radio"
                checked={optimizationTarget === OptimizationTarget.CoursesTaken}
              />
              <div>Minimize Courses Taken</div>
            </li>

            <li
              className={
                "flex flex-row gap-2 hover:cursor-pointer hover:underline"
              }
              onClick={() =>
                setOptimizationTarget(OptimizationTarget.DaysOnCampus)
              }
            >
              <input
                readOnly={true}
                type="radio"
                checked={optimizationTarget === OptimizationTarget.DaysOnCampus}
              />
              <div>Minimize Days On Campus</div>
            </li>

            <li
              className={
                "flex flex-row gap-2 hover:cursor-pointer hover:underline"
              }
              onClick={() =>
                setOptimizationTarget(OptimizationTarget.TimeOnCampus)
              }
            >
              <input
                readOnly={true}
                type="radio"
                checked={optimizationTarget === OptimizationTarget.TimeOnCampus}
              />
              <div>Minimize Time On Campus</div>
            </li>
          </ul>
        </div>
      </div>

      <Button
        onClick={() => genSchedule()}
        className={"bg-lime-700 hover:bg-lime-600"}
      >
        GENERATE
      </Button>
      <div>
        {!scheduleIsLoading && schedule !== null && (
          <WeeklySchedule courses={schedule} />
        )}
        {/*TODO: modal or tooltip wiht course info, diff colours if tut/lab/lecture*/}
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
