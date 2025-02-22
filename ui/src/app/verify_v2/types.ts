export enum CourseType {
  UNKNOWN = 0,
  USER_COMPLETED = 1,
  USER_DESIRED = 2,
  SOLVER_PLANNED = 3,
}

// TODO: these should be snake not camel
export interface CourseSelection {
  id: string; // uuid
  course_name: string;
  course_type: CourseType;
  semester: number;
}

export interface SolverFeedback {
  category: string;
  reason?: string;
  lte?: number;
  gte?: number;
  current?: number;
  contributing_courses: string[];
}

export interface PlanResponse {
  courses: CourseSelection[];
  issues: SolverFeedback[];
}
