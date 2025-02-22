"use client";

import { Input } from "@/components/ui/input";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import processPdf from "@/api/processPdf";
import { useToast } from "@/hooks/use-toast";
import verifyGraduation from "@/api/verifyGraduation";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
} from "@/components/ui/select";

export default function Page() {
  const { toast } = useToast();

  const [file, setFile] = useState(null);
  const [completedCourses, setCompletedCourses] = useState<string>("");
  const [canGraduate, setCanGraduate] = useState<boolean>(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      if (selectedFile.type !== "application/pdf") {
        toast({
          title: "Error",
          description: "File must be PDF",
          variant: "destructive",
        });
        return;
      }

      if (selectedFile.size > 3 * 1024 * 1024) {
        toast({
          title: "Error",
          description: "File must be <3 MB",
          variant: "destructive",
        });
        return;
      }

      setFile(selectedFile);
    }
  };

  const handleFileSubmission = async () => {
    if (!file) {
      toast({
        title: "Error",
        description: "upload file before submission",
        variant: "destructive",
      });

      return;
    }

    try {
      const processPdfResponse = await processPdf(file);
      setCompletedCourses(processPdfResponse.matches.join(", "));
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to process PDF",
        variant: "destructive",
      });
    } finally {
      console.log("done");
    }
  };

  const validateGraduation = async () => {
    if (!completedCourses) {
      toast({
        title: "Error",
        description: "Must have completed courses",
        variant: "destructive",
      });
      return;
    }

    const res = await verifyGraduation(completedCourses);
    setCanGraduate(res.can_graduate);
  };

  return (
    <div className={"space-y-3"}>
      <div className={"flex flex-col md:flex-row gap-4"}>
        <div className={"border border-black md:w-1/2 bg-white space-y-2"}>
          <div
            className={"text-lg p-3 font-semibold border-b border-b-gray-400"}
          >
            Transcript PDF
          </div>
          <div className={"p-3 space-y-2"}>
            <Input
              type="file"
              placeholder="transcript PDF"
              onChange={handleFileChange}
            />
            <Button onClick={handleFileSubmission}> Parse Courses</Button>
          </div>
        </div>

        <div className={"border border-black sm:w-full md:w-1/2 bg-white"}>
          <h3
            className={"text-lg p-3 font-semibold border-b border-b-gray-400"}
          >
            Completed Courses
          </h3>
          <div className={"p-3"}>
            <textarea
              placeholder="Upload your transcript to auto-populate"
              className={"p-2 w-full text-md border-zinc-200 border"}
              value={completedCourses}
              onChange={(e) => setCompletedCourses(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/*TODO multi program maps or custom program map*/}
      <Select>
        <SelectTrigger>Select Course Map</SelectTrigger>
        <SelectContent>
          <SelectGroup>
            <SelectItem value="computer-science">Computer Science</SelectItem>
          </SelectGroup>
        </SelectContent>
      </Select>
      <div className={"text-lg font-semibold"}>
        Program Map Select:{" "}
        <span className={"font-normal"}>Computer Science</span>
      </div>

      <Button
        className={"bg-lime-700 hover:bg-lime-600"}
        onClick={validateGraduation}
      >
        Verify
      </Button>

      <h2 className={"text-lg font-semibold"}>
        {canGraduate !== null && (
          <div className={canGraduate ? `text-green-700` : `text-red-700`}>
            {canGraduate ? "Can Graduate" : "Unable to Graduate"}
          </div>
        )}
      </h2>

      <div className={"text-xs"}>todo: what do i need?</div>
    </div>
  );
}
