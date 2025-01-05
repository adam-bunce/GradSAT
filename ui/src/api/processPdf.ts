interface processPdfResponse {
  matches: string[];
}

export default async function processPdf(
  file: File,
): Promise<processPdfResponse> {
  const forumData = new FormData();
  forumData.append("file", file);

  // high quality code base btw
  //@ts-ignore
  const response = await fetch("http://localhost:8000/process-pdf", {
    method: "POST",
    body: forumData,
  });

  if (!response.ok) {
    throw new Error("Failed to upload PDF");
  }

  return response.json();
}
