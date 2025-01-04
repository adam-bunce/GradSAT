export enum Subjects {
  MATH = "MATH",
  COMPUTER_SCIENCE = "CSCI",
  BIOLOGY = "BIOL",
  PHYSICS = "PHY",
}

export enum DayOfTheWeek {
  MONDAY = "monday",
  TUESDAY = "tuesday",
  WEDNESDAY = "wednesday",
  THURSDAY = "thursday",
  FRIDAY = "friday",
  SATURDAY = "saturday",
  SUNDAY = "sunday",
}

export interface ForcedConflict {
  uuid: string;
  start?: number; // HHMM
  stop?: number; // HHMM
  day?: DayOfTheWeek;
}

export interface FilterConstraint {
  uuid: string;
  course_codes?: string[];
  subjects?: Subjects[];
  year_levels?: number[];
  eq?: number;
  gte?: number;
  lte?: number;
}

export interface Course {
  crn: number;
  name: string;
  meeting_type: string;
  start_time?: number;
  end_time?: number;
}

export type GenerateTimeTableResponse = Partial<Record<DayOfTheWeek, Course[]>>;

export default async function generateTimeTable(
  filterConstraints: FilterConstraint[],
  forcedConflicts: ForcedConflict[],
): Promise<GenerateTimeTableResponse> {
  // TODO remove things where not all 3 are present
  // TODO: read url from config
  const body = {
    forced_conflicts: forcedConflicts.map(({ uuid, ...rest }) => rest),
    filter_constraints: filterConstraints.map(({ uuid, ...rest }) => rest),
  };

  const response = await fetch("http://localhost:8000/time-table", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  // TODO: make more robust
  if (!response.ok) {
    throw new Error("Generate Time Table Response Not OK");
  }

  return response.json();
}
