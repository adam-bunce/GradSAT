"use client";

import { playfair, geist_mono } from "../../styles/fonts";
import Card from "@/components/card";

export default function Home() {
  return (
    <div className={"space-y-10"}>
      <h3 className={`text-5xl mb-16 ${playfair.className} leading-snug`}>
        CP-SAT powered course scheduling and graduation planning.
      </h3>

      <div className={"columns-1 md:columns-3 space-y-4 md:mx-0 lg:-mx-12 "}>
        <Card
          header="Schedule Generation"
          body="Smart schedule generation creates optimized semester schedules based on your preferences for class timings and workload"
          image_url="patchwork.svg"
        />

        <Card
          header="Graduation Verification"
          body="Ensure you graduate on time by verifying your completed courses meet graduation requirements"
          image_url="tree.svg"
        />

        <Card
          header="Course Exploration"
          body="Easily view course offerings with our improved UI & UX"
          image_url="dag.png"
        />
      </div>
    </div>
  );
}
