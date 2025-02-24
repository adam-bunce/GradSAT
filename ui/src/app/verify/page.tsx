"use client";

import { Input } from "@/components/ui/input";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import SemesterCourseInput from "@/components/semester-courses-input";
import courses from "@/courses.json";
import RequirementsStatus from "@/components/requirements-status";
import CoursePreferences from "@/components/course-preferences";
import processPdf from "@/api/processPdf";
import {
  CourseSelection,
  CourseType,
  SolverFeedback,
} from "@/app/verify/types";
import populateTable from "@/api/populateTable";
import verifyGraduation from "@/api/verifyGraduation";

export default function Page() {
  const { toast } = useToast();

  const [file, setFile] = useState(null);
  const [canGraduate, setCanGraduate] = useState<boolean>(null);
  const [courseMap, setCourseMap] = useState<string>(null);
  const [semesters, setSemesters] = useState(8);
  const [userCourseInputInitial, setUserCourseInputInitial] = useState<
    CourseSelection[]
  >([]);
  const [userCourseInput, setUserCourseInput] = useState<CourseSelection[]>([]);
  const [solverFeedback, setSolverFeedback] = useState<SolverFeedback[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isFeedbackLoading, setIsFeedbackLoading] = useState(false);
  const [userHasSubmitted, setUserHasSubmitted] = useState(false);
  const [courseStarPreferences, setCourseStarPreferences] = useState([]);

  const validateGraduation = async () => {
    setUserHasSubmitted(true);
    setIsFeedbackLoading(true);
    let taken_in = [];
    let completed_in = [];

    for (let course of userCourseInput) {
      const exists = course.course_type;

      if (exists) {
        taken_in.push([course.course_name.toUpperCase(), course.semester]);
      }
    }

    try {
      const res = await verifyGraduation(taken_in, completed_in);
      setSolverFeedback(res.issues);
    } catch (err) {
      toast({
        title: "Error",
        description: `Failed to verify graduation requirements.`,
        variant: "destructive",
      });
    }

    setIsFeedbackLoading(false);
  };

  const clearSuggestions = () => {
    setUserCourseInputInitial((prevCourses) =>
      prevCourses.filter(
        (course) => course.course_type != CourseType.SOLVER_PLANNED,
      ),
    );
  };

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
      setUserCourseInputInitial(processPdfResponse);
    } catch (err) {
      toast({
        title: "Error",
        description: "Failed to process PDF",
        variant: "destructive",
      });
    }
  };

  const fillInBlanks = async () => {
    let taken_in = [];
    let completed_in = [];

    for (let course of userCourseInput) {
      const is_desired = course.course_type == CourseType.USER_DESIRED;
      const is_completed = course.course_type == CourseType.USER_COMPLETED;
      const exists = course.course_type;

      if (exists && is_desired) {
        taken_in.push([course.course_name.toUpperCase(), course.semester]);
      } else if (exists && is_completed) {
        completed_in.push([course.course_name.toUpperCase(), course.semester]);
      }
    }

    setUserHasSubmitted(true);
    setIsLoading(true);
    const tmp = Object.entries(courseStarPreferences).map(([k, v]) => [k, v]);

    try {
      const res = await populateTable(taken_in, completed_in, tmp);

      console.log(res);

      setSolverFeedback(res.issues);
      if (res.courses.length == 0) {
        toast({
          title: "Error",
          description: `Failed to populate courses, user defined courses already invalid.`,
          variant: "destructive",
        });
      } else {
        setUserCourseInputInitial(res.courses);
      }
    } catch (err) {
      toast({
        title: "Error",
        description: `Failed to populate courses, error from server.`,
        variant: "destructive",
      });
    }

    setIsLoading(false);
  };

  return (
    <div className={"space-y-3 lg:-mx-12"}>
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
            <span className={"text-lg"}>
              TODO: modify/view before adding to course plan
            </span>
          </div>
        </div>
      </div>

      <div className={"py-3"}></div>
      <div className={"flex flex-col md:flex-row gap-3"}>
        <div className={"border border-black md:w-2/3 bg-white space-y-2"}>
          <div
            className={"text-lg p-3 font-semibold border-b border-b-gray-400"}
          >
            Course Plan
          </div>
          <div className={"p-3 space-y-2"}>
            <SemesterCourseInput
              courses={courses.courses}
              initial={userCourseInputInitial}
              updateParentData={setUserCourseInput}
              isLoading={isLoading}
            />
          </div>
        </div>

        <div className={"sm:w-full md:w-1/3 flex flex-col gap-3"}>
          <div className={"border border-black sm:w-full bg-white h-1/2"}>
            <h3
              className={"text-lg p-3 font-semibold border-b border-b-gray-400"}
            >
              Graduation Requirement Status
              <span className={"text-md text-zinc-500"}>
                {solverFeedback.length
                  ? " (" + solverFeedback.length.toString() + ")"
                  : ""}
              </span>
            </h3>
            <div className={"p-3"}>
              <RequirementsStatus
                issues={solverFeedback}
                isLoading={isLoading || isFeedbackLoading}
                hasSubmitted={userHasSubmitted}
              />
            </div>
          </div>

          <div className={"border border-black sm:w-full bg-white h-1/2"}>
            <h3
              className={"text-lg p-3 font-semibold border-b border-b-gray-400"}
            >
              Course Preferences
            </h3>
            <div className={"p-3"}>
              <CoursePreferences
                courses={courses.courses}
                setParentPreferences={setCourseStarPreferences}
              />
            </div>
          </div>
        </div>
      </div>

      <div className={"flex flex-row gap-2"}>
        <Button
          className={"bg-lime-700 hover:bg-lime-600"}
          onClick={validateGraduation}
        >
          Verify
        </Button>

        <Button
          className={"bg-sky-700 hover:bg-sky-600"}
          onClick={fillInBlanks}
        >
          Auto-Populate
        </Button>

        <Button
          className={"bg-red-700 hover:bg-red-600"}
          onClick={clearSuggestions}
        >
          Clear
        </Button>
      </div>

      <h2 className={"text-lg font-semibold"}>
        {canGraduate !== null && (
          <div className={canGraduate ? `text-green-700` : `text-red-700`}>
            {canGraduate ? "Can Graduate" : "Unable to Graduate"}
          </div>
        )}
      </h2>
    </div>
  );
}
