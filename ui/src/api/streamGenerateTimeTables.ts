import { FilterConstraint, ForcedConflict } from "@/api/generateTimeTable";

export default async function getEvents(
  filterConstraints: FilterConstraint[],
  forcedConflicts: ForcedConflict[],
  onEvent: (event: any) => void,
) {
  const body = {
    forced_conflicts: forcedConflicts.map(({ uuid, ...rest }) => rest),
    filter_constraints: filterConstraints.map(({ uuid, ...rest }) => rest),
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
    console.log("received", value, "iter", iter);
    // console.log("received", JSON.parse(value));
  }
}
