import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import CourseSearch from "@/components/course-search";
import { useEffect, useState } from "react";
import { CourseSelection, CourseType } from "@/app/verify/types";
import { Button } from "@/components/ui/button";

const courseTypeToColour = new Map<CourseType, string>([
  [CourseType.UNKNOWN, "hover:border-gray-400 border-gray-200"],
  [CourseType.USER_COMPLETED, "bg-zinc-100 cursor-not-allowed border-zinc-100"],
  [
    CourseType.USER_DESIRED,
    "bg-sky-600 hover:bg-sky-700 border-sky-600 text-white",
  ],
  [CourseType.SOLVER_PLANNED, "bg-lime-600 hover:bg-lime-700 border-lime-600"],
]);

function render_semester(
  completed_courses: CourseSelection[],
  semester: number,
  courses_per_semester: number,
  callback,
  setDialogState,
) {
  let courses_in_semester = [];
  completed_courses.forEach((item) => {
    if (item.semester === semester) {
      courses_in_semester.push(item);
    }
  });

  // maintain order in semester based on uuid
  courses_in_semester.sort((a, b) => a.id.localeCompare(b.id));

  let items = [];
  for (let i = 0; i < courses_per_semester; i++) {
    items.push(
      <DialogTrigger
        onClick={() => {
          callback(courses_in_semester[i]?.id);
          setDialogState(true);
        }}
        key={i}
      >
        <div
          className={
            "px-2 py-1 border rounded-[2px] " +
            courseTypeToColour.get(courses_in_semester[i]?.course_type)
          }
        >
          {courses_in_semester[i]?.course_name
            ? courses_in_semester[i]?.course_name.toUpperCase()
            : "..."}
        </div>
      </DialogTrigger>,
    );
  }

  return items;
}

const init_courses = (existing: CourseSelection[]): CourseSelection[] => {
  const SEMESTERS = 8;
  const COURSES_PER_SEMESTER = 5;
  let res: CourseSelection[] = [];

  for (let semester = 1; semester <= SEMESTERS; semester += 1) {
    for (let course = 1; course <= COURSES_PER_SEMESTER; course += 1) {
      res.push({
        course_name: "",
        course_type: CourseType.UNKNOWN,
        semester: semester,
        id: `s${semester}_c${course}`,
      });
    }
  }

  // kinda bad
  for (let course of existing) {
    for (let toReplace of res) {
      if (
        toReplace.course_name == "" &&
        toReplace.semester == course.semester
      ) {
        toReplace.course_name = course.course_name;
        toReplace.course_type = course.course_type;
        break;
      }
    }
  }

  return res;
};

export default function SemesterCourseInput({
  courses,
  initial,
  updateParentData,
  isLoading,
}) {
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [selectedCourseId, setSelectedCourseId] = useState("");
  const [userCourseInput, setUserCourseInput] = useState<CourseSelection[]>([]);

  useEffect(() => {
    const data = init_courses(initial);
    console.log("data", data);
    setUserCourseInput(data);
    updateParentData(data);
  }, [initial]);
  const setUserCourse = (
    id: string,
    course_name: string,
    course_type: CourseType | null,
  ) => {
    let updatedCourse = userCourseInput.find(
      (userCourse) => userCourse.id === id,
    );

    if (!updatedCourse) return;
    updatedCourse.course_name = course_name;
    updatedCourse.course_type = CourseType.USER_DESIRED;
    if (course_type !== null) {
      updatedCourse.course_type = course_type;
    }

    setUserCourseInput([
      ...userCourseInput.filter((course) => course.id !== id),
      updatedCourse,
    ]);

    updateParentData([
      ...userCourseInput.filter((course) => course.id !== id),
      updatedCourse,
    ]);
  };

  if (isLoading) {
    return (
      <div className={"space-y-1"}>
        {Array.from({ length: 8 }).map((_, sem_idx) => (
          <div key={sem_idx}>
            <h4 className={"font-medium"}> Semester {sem_idx + 1}</h4>
            <div className={"grid grid-cols-5 gap-1"}>
              {Array(5)
                .fill(null)
                .map(() => {
                  return (
                    <div
                      className={
                        "bg-zinc-400 animate-pulse h-8 rounded-[2px] px-2 py-1"
                      }
                    ></div>
                  );
                })}
            </div>

            {(sem_idx + 1) % 2 == 0 && sem_idx + 1 != 8 && (
              <div className={"divider py-3"}></div>
            )}
          </div>
        ))}
      </div>
    );
  }

  return (
    <Dialog
      open={dialogOpen}
      onOpenChange={(newOpenState) => setDialogOpen(newOpenState)}
    >
      <DialogContent
        aria-describedby={
          "dialog for selecting/modifying user completed courses"
        }
      >
        <DialogTitle>
          {userCourseInput.some(
            (course) =>
              course.id == selectedCourseId && course.course_name !== "",
          )
            ? "Modifying " +
              userCourseInput
                .find((course) => course.id == selectedCourseId)
                ?.course_name.toUpperCase()
            : "Select Desired Course"}
        </DialogTitle>

        <div>
          <CourseSearch
            courses={courses}
            onChange={(ev) => {
              setUserCourse(
                selectedCourseId,
                ev.target.innerText,
                CourseType.USER_DESIRED,
              );
              setDialogOpen(!dialogOpen);
            }}
          />
        </div>
        <DialogFooter>
          <Button
            variant={"destructive"}
            onClick={() => {
              setUserCourse(selectedCourseId, "", CourseType.UNKNOWN);
              setDialogOpen(false);
            }}
          >
            Remove
          </Button>
        </DialogFooter>
      </DialogContent>

      <div className={"space-y-1"}>
        {Array.from({ length: 8 }).map((_, sem_idx) => (
          <div key={sem_idx}>
            <h4 className={"font-medium"}> Semester {sem_idx + 1}</h4>
            <div className={"grid grid-cols-5 gap-1"}>
              {render_semester(
                userCourseInput,
                sem_idx + 1,
                5,
                setSelectedCourseId,
                setDialogOpen,
              )}
            </div>

            {(sem_idx + 1) % 2 == 0 && sem_idx + 1 != 8 && (
              <div className={"divider py-3"}></div>
            )}
          </div>
        ))}
      </div>
    </Dialog>
  );
}
