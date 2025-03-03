import { VerifyResponse } from "@/app/verify/types";

interface graduationVerificationResponse {
  can_graduate: boolean;
}

export default async function verifyGraduation(
  taken_in: [][],
  completed_courses: [][],
  must_take: string[],
  must_not_take: string[],
): Promise<VerifyResponse> {
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
    must_take: must_take,
    must_not_take: must_not_take,
  };

  const response = await fetch(
    process.env.NEXT_PUBLIC_API_URL + "/graduation-verification",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );

  // NOTE: do i want to do errors here or in the component
  if (!response.ok) {
    throw new Error("Failed to verify graduation requirements");
  }

  return response.json();
}
