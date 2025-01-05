import { Course, DayOfTheWeek } from "@/api/generateTimeTable";
// React import gets rid of ts errors?
import React, { useEffect, useRef } from "react";
import { gen_time_labels } from "@/components/window-select";
import Form from "next/form";

const CONTAINER_HEIGHT = 960;
const DAY_MINUTES = 24 * 60;
const TIME_SCALE = CONTAINER_HEIGHT / DAY_MINUTES;

function Col({ dayCourses }: { dayCourses: Course[] }) {
  const calculatePos = (course: Course): Object => {
    if (!course) return {};

    const startMinutes =
      Math.floor(course.start_time / 100) * 60 + (course.start_time % 100);

    const endMinutes =
      Math.floor(course.end_time / 100) * 60 + (course.end_time % 100);

    const courseHeight = Math.floor((endMinutes - startMinutes) * TIME_SCALE);
    const courseTop = startMinutes * TIME_SCALE;

    return {
      position: "absolute",
      top: courseTop,
      height: courseHeight,
      backgroundColor: "#fb923c",
    };
  };

  return (
    <div className={"h-[960px] relative"}>
      {dayCourses.map((course) => (
        <div
          key={course.crn}
          style={calculatePos(course)}
          className={"w-full px-1 text-sm"}
        >
          {course.name}
          <div>
            {course.start_time} - {course.end_time}
          </div>
        </div>
      ))}
    </div>
  );
}

// TODO: compact view would be nice
export default function WeeklySchedule({ courses }) {
  const timeLabels = gen_time_labels().filter((_, idx) => idx % 4 == 0);
  const labelHeight = Math.floor(CONTAINER_HEIGHT / timeLabels.length);
  const scheduleRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // scroll schedule 75%  down where courses will most likley be
    if (scheduleRef.current) {
      const container = scheduleRef.current;
      container.scrollTop =
        (container.scrollHeight - container.clientHeight) * (3 / 4);
    }
  }, []);

  return (
    <div className={"overflow-scroll bg-white"}>
      <div className={"border-green-300 w-full min-w-[650px]"}>
        <div className={"grid grid-cols-8"}>
          <div className={"bg-white"}>{/* empty cell */}</div>
          {Object.values(DayOfTheWeek).map((dotw, idx) => (
            <div key={idx} className={"bg-white"}>
              {dotw.toUpperCase().slice(0, 3)}
            </div>
          ))}
        </div>

        <div
          className={
            "border-t border-gray-400  grid grid-cols-8 h-[600px] bg-white"
          }
          ref={scheduleRef}
        >
          <div className={"border-r border-gray-400"}>
            {timeLabels.map((pair, idx) => (
              <div
                className={
                  "border-b border-black h-[960px] flex flex-row justify-end"
                }
                style={{ height: labelHeight + "px" }}
                key={idx}
              >
                {pair[0]}
              </div>
            ))}
          </div>

          {Object.values(DayOfTheWeek).map((dotw, idx) => (
            <div className={"border-r border-gray-400"} key={idx}>
              <Col dayCourses={courses[dotw] ? courses[dotw] : []} />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
