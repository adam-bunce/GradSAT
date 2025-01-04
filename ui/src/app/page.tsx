import { playfair } from "../../styles/fonts";
import Card from "@/components/card";

export default function Home() {
  return (
    <div className={"space-y-16"}>
      <h3 className={`text-5xl ${playfair.className} leading-snug`}>
        CP-SAT powered course scheduling and graduation planning.
      </h3>

      <div className={"columns-1 md:columns-3 space-y-4 md:mx-0 lg:-mx-12 "}>
        <Card
          header="Schedule Generation"
          body="Smart schedule generation creates optimized semester schedules based on your preferences for class timings and workload"
          image_url="robot.jpg"
        />

        <Card
          header="Graduation Verification"
          body="Graduation Path Verification Automatically verify if your current course selection meets all graduation requirements and prerequisites"
          image_url="ceg.png"
        />

        <Card
          header="Course Exploration"
          body="Ergonomically view course offerings with our improved UI/UX"
          image_url="dag.png"
        />
      </div>

      <div className={"divider md:mx-0 lg:-mx-12 "}></div>

      <div className={"columns-2"}>
        <div>
          Lorem ipsum dolor sit amet, consectetur adipisicing elit. A aspernatur
          autem blanditiis, cumque deserunt distinctio, doloremque facilis
          impedit in ipsam magnam molestias necessitatibus neque officiis
          possimus quaerat quas quod suscipit.
        </div>

        <div className={"border-l border-l-black"}>
          Lorem ipsum dolor sit amet, consectetur adipisicing elit. A aspernatur
          autem blanditiis, cumque deserunt distinctio, doloremque facilis
          impedit in ipsam magnam molestias necessitatibus neque officiis
          possimus quaerat quas quod suscipit.
        </div>
      </div>

      <div>
        <h6>How it works</h6>
        <ol>
          <li>
            Data Collection Our system automatically collects and processes
            current course offerings and their prerequisites using advanced web
            scraping techniques
          </li>
          <li>
            Constraint Processing Course requirements are parsed and transformed
            into a formal logic structure using ANTLR grammar and DNF formatting
          </li>
          <li>
            Schedule Optimization SAT solver applies your preferences and
            academic requirements to generate optimal course schedules
          </li>
        </ol>
      </div>
    </div>
  );
}
