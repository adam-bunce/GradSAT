import { geist_mono } from "../../styles/fonts";
import { useState } from "react";

enum DayOfTheWeek {
  MONDAY = "monday",
  TUESDAY = "tuesday",
  WEDNESDAY = "wednesday",
  THURSDAY = "thursday",
  FRIDAY = "friday",
  SATURDAY = "saturday",
  SUNDAY = "sunday",
}

export default function Calendar() {
  const [dayOfWeek, setDayOfWeek] = useState<DayOfTheWeek>(null);
  const [initialClickY, setInitialClickY] = useState<number>(null);
  const [finalClickY, setFinalClickY] = useState<number>(null);
  const [mouseDown, setMouseDown] = useState(false);

  const select = () => {
    if (!mouseDown) return;
  };

  return (
    <>
      <div>{dayOfWeek}</div>
      <div>init {initialClickY}</div>
      <div>fnl {finalClickY}</div>
      <div className={"columns-8 border gap-0"}>
        <div className={"flex flex-col w-full justify-between min-h-[961px] "}>
          {[...Array(12)].map((_, hour) => (
            <div
              key={hour}
              className={"text-right text-gray-500 text-sm border-none"}
            >
              {hour + 1} am
            </div>
          ))}

          {[...Array(12)].map((_, hour) => (
            <div key={hour} className={"text-right text-gray-500 text-sm"}>
              {hour + 1} pm
            </div>
          ))}
        </div>

        {Object.values(DayOfTheWeek).map((dotw, idx) => (
          <div
            key={idx}
            onMouseDown={(event) => {
              setDayOfWeek(dotw as DayOfTheWeek);
              setInitialClickY(event.nativeEvent.offsetY);
              setMouseDown(true);
            }}
            onMouseUp={(event) => {
              setFinalClickY(event.nativeEvent.offsetY);
              setMouseDown(false);
            }}
            className={`min-w-12 border min-h-[961px] break-inside-avoid-column text-center uppercase ${geist_mono.className}`}
          >
            {dotw.slice(0, 3)}
          </div>
        ))}
      </div>
    </>
  );
}
