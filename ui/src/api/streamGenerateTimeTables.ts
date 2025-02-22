import {
  FilterConstraint,
  ForcedConflict,
  GenerateTimeTableResponse,
  OptimizationTarget,
} from "@/api/generateTimeTable";
import { Property } from "csstype";
import Filter = Property.Filter;

export default async function getEvents(
  filterConstraints: FilterConstraint[],
  forcedConflicts: ForcedConflict[],
  optimizationTarget: OptimizationTarget,
  onEvent: (event: GenerateTimeTableResponse) => void,
) {
  // TODO: pull this out into a method generateTimeTable also does this, ts Omit<>
  const filter_constraints = filterConstraints.map(({ uuid, ...rest }) => rest);

  for (let i = 0; i < filter_constraints.length; i++) {
    const targets = ["eq", "lte", "gte"];

    for (const target of targets) {
      if (
        filter_constraints[i][target as keyof Omit<FilterConstraint, "uuid">] ==
        ""
      ) {
        delete filter_constraints[i][
          target as keyof Omit<FilterConstraint, "uuid">
        ];
      }
    }
  }

  const body = {
    forced_conflicts: forcedConflicts.map(({ uuid, ...rest }) => rest),
    filter_constraints: filter_constraints,
    optimization_target: optimizationTarget,
  };

  const response = await fetch("http://localhost:8000/all-time-tables", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
  let iter = 0;
  while (true) {
    const { value, done } = await reader.read();
    iter += 1;
    if (done) {
      console.log("break!");
      break;
    }

    const data = value?.split("data:")[1];
    const schedule = JSON.parse(data);
    onEvent(schedule);
  }
}
