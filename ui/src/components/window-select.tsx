import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

import { DayOfTheWeek } from "@/api/generateTimeTable";

function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1, str.length).toLowerCase();
}

type TimePair = [number, string];

// if this isnt going to be rendered every time, should i pull it out of this function?
export const gen_time_labels = (): TimePair[] => {
  let times = [];
  for (let hour = 0; hour < 24; hour++) {
    for (let minute = 0; minute < 46; minute += 15) {
      // NOTE im getting 0:15 right now for 12:15 fix eventually
      let hours = (hour % 12).toString();
      if (hours == 0) hours = "12";
      const minutes = minute.toString().padEnd(2, "0");
      const period = hour % 12 != hour ? "pm" : "am";

      const humanTime = `${hours}:${minutes}${period}`;
      const militaryTime = Number(hour.toString() + minutes.toString());

      times.push([humanTime, militaryTime]);
    }
  }

  return times;
};

const times = gen_time_labels();

export default function WindowSelect({
  uuid,
  startTime,
  stopTime,
  dayOfTheWeek,
  onChange,
}) {
  const isDisabled = () => {
    if (!startTime) return true;
    if (!stopTime) return true;
    if (!dayOfTheWeek) return true;

    return false;
  };

  return (
    <div
      className={`flex flex-row space-x-2 ${isDisabled() ? "opacity-75" : ""}`}
    >
      <Select
        onValueChange={(dayOfTheWeek) => {
          onChange(uuid, "day", dayOfTheWeek);
        }}
        value={dayOfTheWeek}
      >
        <SelectTrigger className="w-[120px]">
          <SelectValue placeholder="Day" />
        </SelectTrigger>
        <SelectContent>
          <>
            {Object.keys(DayOfTheWeek).map((dayOfWeek, _) => (
              <SelectItem value={dayOfWeek.toUpperCase()} key={dayOfWeek}>
                {capitalize(dayOfWeek)}
              </SelectItem>
            ))}
          </>
        </SelectContent>
      </Select>
      <Select
        onValueChange={(startTimeValue) =>
          onChange(uuid, "start", startTimeValue)
        }
        value={startTime}
      >
        <SelectTrigger className="w-[120px]">
          <SelectValue placeholder="Start Time" />
        </SelectTrigger>
        <SelectContent>
          <>
            {times.map(([humanTime, militaryTime], _) => (
              <SelectItem value={militaryTime} key={militaryTime}>
                {humanTime}
              </SelectItem>
            ))}
          </>
        </SelectContent>
      </Select>

      <div className={"flex items-center"}>–</div>

      <Select
        onValueChange={(endTimeValue) => onChange(uuid, "stop", endTimeValue)}
        value={stopTime}
      >
        <SelectTrigger className="w-[120px]">
          <SelectValue placeholder="End Time" />
        </SelectTrigger>
        <SelectContent>
          <>
            {times.map(([humanTime, militaryTime], _) => (
              <SelectItem value={militaryTime} key={militaryTime}>
                {humanTime}
              </SelectItem>
            ))}
          </>
        </SelectContent>
      </Select>
    </div>
  );
}
