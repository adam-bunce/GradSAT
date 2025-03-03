"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { useEffect, useState } from "react";
import { Star, ThumbsUp, ThumbsDown } from "lucide-react";
import { Input } from "@/components/ui/input";
import { printDebugThrownValueForProspectiveRender } from "next/dist/server/app-render/prospective-render-utils";

const rating_to_colours = {
  1: "text-red-500 fill-red-500",
  2: "text-orange-500 fill-orange-500",
  3: "text-black-400 fill-black-400",
  4: "text-lime-500 fill-lime-500",
  5: "text-green-500 fill-green-500",
};

export default function CoursePreferences({
  courses,
  setParentPreferences,
  setParentLikes,
  setParentDislikes,
}) {
  const [courseRatings, setCourseRatings] = useState({});
  const [searchTerm, setSearchTerm] = useState("");
  const [likes, setLikes] = useState({});
  const [dislikes, setDislikes] = useState({});

  useEffect(() => {
    const initialRatings = Object.fromEntries(
      courses.map((course) => [course, 3]),
    );

    const initialLikes = Object.fromEntries(
      courses.map((course) => [course, false]),
    );
    setLikes(initialLikes);
    setParentLikes(initialLikes);
    setDislikes(initialLikes);
    setParentDislikes(initialLikes);

    setCourseRatings(initialRatings);
    setParentPreferences(initialRatings);
  }, [courses]);

  const updateRating = (courseName, newRating) => {
    setCourseRatings((prev) => ({ ...prev, [courseName]: newRating }));
    setParentPreferences((prev) => ({ ...prev, [courseName]: newRating }));
  };

  const updateLike = (courseName, currentValue) => {
    setLikes((prev) => ({ ...prev, [courseName]: !currentValue }));
    setDislikes((prev) => ({ ...prev, [courseName]: false }));

    setParentLikes((prev) => ({ ...prev, [courseName]: !currentValue }));
    setParentDislikes((prev) => ({ ...prev, [courseName]: false }));
  };
  const updateDislikes = (courseName, currentValue) => {
    setDislikes((prev) => ({ ...prev, [courseName]: !currentValue }));
    setLikes((prev) => ({
      ...prev,
      [courseName]: false,
    }));

    setParentDislikes((prev) => ({ ...prev, [courseName]: !currentValue }));
    setParentLikes((prev) => ({
      ...prev,
      [courseName]: false,
    }));
  };

  return (
    <div>
      <Input
        placeholder={"Search Course Codes"}
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      <ScrollArea className={"h-56 space-y-2 pt-0 pb-3"}>
        {courses
          .filter((course) =>
            course.toLowerCase().includes(searchTerm.toLowerCase()),
          )
          .map((course) => (
            <div
              key={course}
              className={"flex flex-row justify-between space-y-4 "}
            >
              <div
                className={
                  "flex flex-row items-end w-6/12 " +
                  rating_to_colours[courseRatings[course]]
                }
              >
                {course}
              </div>
              <div className={"flex flex-row w-3/12"}>
                <ThumbsUp
                  onClick={() => updateLike(course, likes[course])}
                  className={`p-1 w-6 h-6 fill-none text-gray-400 cursor-pointer  rounded-md ${likes[course] == true ? "bg-green-200 hover:bg-green-300" : "hover:bg-gray-100"}`}
                />
                <ThumbsDown
                  onClick={() => updateDislikes(course, dislikes[course])}
                  className={`p-1 w-6 h-6 fill-none text-gray-400 cursor-pointer  rounded-md ${dislikes[course] == true ? "bg-red-200 hover:bg-red-300" : "hover:bg-gray-100"}`}
                />
              </div>
              <div className={"flex flex-row pr-3"}>
                <div className="flex flex-row ">
                  {[1, 2, 3, 4, 5].map((rating, idx) => (
                    <Star
                      className={`w-5 h-5 fill-none text-yellow-400 cursor-pointer  hover:fill-yellow-300
                                ${courseRatings[course] >= rating ? "fill-yellow-400" : ""}`}
                      key={rating}
                      onClick={() => {
                        updateRating(course, rating);
                      }}
                    />
                  ))}
                </div>
              </div>
            </div>
          ))}
      </ScrollArea>
    </div>
  );
}
