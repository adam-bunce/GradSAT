"use client";

import { ScrollArea } from "@/components/ui/scroll-area";
import { useEffect, useState } from "react";
import { Circle, Star, StarHalf, StarOff } from "lucide-react";
import { Input } from "@/components/ui/input";

const rating_to_colours = {
  1: "text-red-500 fill-red-500",
  2: "text-orange-500 fill-orange-500",
  3: "text-zinc-400 fill-zinc-400",
  4: "text-lime-500 fill-lime-500",
  5: "text-green-500 fill-green-500",
};

export default function CoursePreferences({ courses, setParentPreferences }) {
  const [courseRatings, setCourseRatings] = useState({});
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const initialRatings = Object.fromEntries(
      courses.map((course) => [course, 3]),
    );
    setCourseRatings(initialRatings);
    setParentPreferences(initialRatings);
  }, [courses]);

  const updateRating = (courseName, newRating) => {
    setCourseRatings((prev) => ({ ...prev, [courseName]: newRating }));
    setParentPreferences((prev) => ({ ...prev, [courseName]: newRating }));
  };

  return (
    <div>
      <Input
        placeholder={"Search Droppable Codes"}
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
      />

      <ScrollArea className={"h-56 space-y-2 pt-0 pb-3"}>
        {courses
          .filter((course) =>
            course.toLowerCase().includes(searchTerm.toLowerCase()),
          )
          .map((course) => (
            <div key={course} className={"flex flex-row justify-between"}>
              <div
                className={
                  "flex flex-row " + rating_to_colours[courseRatings[course]]
                }
              >
                {course}
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
