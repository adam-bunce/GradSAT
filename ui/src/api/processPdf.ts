import { CourseSelection } from "@/app/verify_v2/types";

interface processPdfResponse {
  matches: string[];
}

export default async function processPdf(
  file: File,
): Promise<CourseSelection[]> {
  const forumData = new FormData();
  forumData.append("file", file);

  // high quality code base btw
  //@ts-ignore
  const response = await fetch(
    process.env.NEXT_PUBLIC_API_URL + "/process-pdf",
    {
      method: "POST",
      body: forumData,
    },
  );

  if (!response.ok) {
    throw new Error("Failed to upload PDF");
  }

  let cc: CourseSelection[] = [];
  const res = await response.json();
  let counter = 0;
  for (let completed_course of res) {
    cc.push({
      id: counter.toString() + completed_course["semester"],
      course_name: completed_course["course_name"],
      semester: completed_course["semester"] + 1,
      course_type: completed_course["course_type"],
    });
  }

  return cc;
}
