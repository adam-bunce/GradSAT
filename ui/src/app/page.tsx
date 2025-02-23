import { playfair, geist_mono } from "../../styles/fonts";
import Card from "@/components/card";

export default function Home() {
  return (
    <div className={"space-y-10"}>
      <pre>{JSON.stringify(process.env, null, 2)}</pre>

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
          header="Droppable Exploration"
          body="Easily view course offerings with our improved UI & UX"
          image_url="dag.png"
        />
      </div>

      <div className={"divider"}></div>

      <div>
        <h2 className={`text-2xl font-semibold`}>How It Works</h2>
        <ol className={"space-y-2"}>
          <li>
            <h3 className={`text-lg font-semibold`}>Scrape:</h3>
            <div className={"pl-2"}>
              The system checks for updates to course offerings{" "}
              <a
                href="https://crontab.guru/#0_01,12_*_*_*"
                className={"underline font-medium"}
              >
                twice a day
              </a>
              {", "}
              and extracts the relevant information.
            </div>
          </li>
          <li>
            <h3 className={`text-lg font-semibold`}>Store:</h3>
            <div className={"pl-2"}>
              The scraped data is stored in an Aurora Postgres DB for later use.
            </div>
          </li>
          <li>
            <h3 className={`text-lg font-semibold`}>Solve:</h3>
            <div className={"pl-2"}>
              Several{" "}
              <a
                href="https://developers.google.com/optimization/cp/cp_solver"
                className={"underline font-medium"}
              >
                CP SAT
              </a>{" "}
              models, tuned to user created constraints, are used to produce
              actionable outputs.
            </div>
          </li>
        </ol>
      </div>
    </div>
  );
}
