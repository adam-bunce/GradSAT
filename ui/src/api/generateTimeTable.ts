export enum OptimizationTarget {
  UNKNOWN = 0,
  CoursesTaken = 1,
  DaysOnCampus = 2,
  TimeOnCampus = 3,
}

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
  eq?: number | "";
  gte?: number | "";
  lte?: number | "";
}

export interface Course {
  crn: number;
  name: string;
  meeting_type: string;
  start_time?: number;
  end_time?: number;
}

export type CourseList = Partial<Record<DayOfTheWeek, Course[]>>;

export interface GenerateTimeTableResponse {
  courses: CourseList;
  found_solution: boolean;
}

export default async function generateTimeTable(
  filterConstraints: FilterConstraint[],
  forcedConflicts: ForcedConflict[],
  optimizationTarget: OptimizationTarget,
): Promise<GenerateTimeTableResponse> {
  // controlled forum cannot be undefined, so remove empty strings
  let filter_constraints = filterConstraints.map(({ uuid, ...rest }) => rest);
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

  console.log(body);

  const response = await fetch(
    process.env.NEXT_PUBLIC_API_URL + "/time-table",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );

  if (!response.ok) {
    throw new Error("Generate Time Table Response Not OK");
  }

  return response.json();
}
