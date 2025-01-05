interface graduationVerificationResponse {
  can_graduate: boolean;
}

export default async function verifyGraduation(
  completed_courses: string,
): Promise<graduationVerificationResponse> {
  completed_courses = completed_courses.replace(/ /g, "");
  const completed_courses_arr = completed_courses.split(",");

  const response = await fetch(
    "http://localhost:8000/graduation-verification",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ completed_courses: completed_courses_arr }),
    },
  );

  // NOTE: do i want to do errors here or in the component
  if (!response.ok) {
    throw new Error("Failed to verify graduation requirements");
  }

  return response.json();
}
