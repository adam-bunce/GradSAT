import { CourseSelection, PlanResponse } from "@/app/verify/types";

// class GeneratePlanRequest(BaseModel):
// completed_courses: list[str]
// taken_in: list[tuple[str, int]]
// course_map: Literal["computer-science"]
// semester_layout: dict[str, int]  # semester name -> # of courses person wants to take

export default async function populateTable(
  taken_in: [][],
  completed_courses: [][],
  course_ratings: [][],
): Promise<PlanResponse> {
  const body = {
    completed_courses: completed_courses,
    taken_in: taken_in,
    course_map: "computer-science",
    semester_layout: {
      Y1_Fall: 1,
      Y1_Winter: 2,
      Y2_Fall: 3,
      Y2_Winter: 4,
      Y3_Fall: 5,
      Y3_Winter: 6,
      Y4_Fall: 7,
      Y4_Winter: 8,
    },
    course_ratings: course_ratings,
  };

  const response = await fetch(
    process.env.NEXT_PUBLIC_API_URL + "/planner-generate",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );

  // NOTE: do i want to do errors here or in the component
  if (!response.ok) {
    throw new Error("Failed to plan ahead");
  }

  const tmp = await response.json();
  console.log(tmp);
  return tmp;
}
