import { useEffect, useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export default function CourseSearch({ courses, onChange }) {
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const FILTER_LIMIT = 8;

  const filterSuggestions = (value) => {
    if (!value) {
      return courses.slice(0, FILTER_LIMIT);
    }

    const filtered = courses.filter((option) =>
      option.toLowerCase().includes(value.toLowerCase()),
    );
    return filtered.slice(0, FILTER_LIMIT);
  };

  useEffect(() => {
    setRecommendations(filterSuggestions(""));
  }, []);

  return (
    <div>
      <Input
        placeholder={"Search For A Droppable"}
        onChange={(event) =>
          setRecommendations(filterSuggestions(event.target.value))
        }
      />

      <div className={"grid grid-cols-4 pt-2 gap-1"}>
        {recommendations.map((recommendation) => (
          <Button
            type="submit"
            variant={"outline"}
            key={recommendation}
            onClick={(event) => onChange(event)}
          >
            {recommendation}
          </Button>
        ))}
      </div>
    </div>
  );
}
