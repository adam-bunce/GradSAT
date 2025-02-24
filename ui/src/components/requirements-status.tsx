import { AlertCircle, CheckCircle, InfoIcon } from "lucide-react";
import { Fragment } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";

export interface SolverFeedback {
  category: string;
  reason?: string;
  lte?: number;
  gte?: number;
  current?: number;
}

const SolverFeedbackToWidget = (feedback: SolverFeedback, id: number) => {
  const calculateRange = (feedback: SolverFeedback) => {
    if (feedback.lte && feedback.gte)
      return `${feedback.lte} - ${feedback.gte} credit hours`;
    if (feedback.lte) return `${feedback.lte} credit hours or less`;
    if (feedback.gte) return `${feedback.gte}+ credit hours`;
  };

  return (
    <Fragment key={id}>
      <div className={"flex items-center gap-3"}>
        <AlertCircle className={"w-5 h-5 text-red-500 flex-shrink-0"} />
        <div className={"flex flex-col"}>
          <div className={"font-medium"}>{feedback.category}</div>
          {feedback.current != null ? (
            <div className={"text-zinc-600 text-sm"}>
              {" "}
              {calculateRange(feedback)} | current: {feedback.current}hrs
            </div>
          ) : (
            <div className={"text-zinc-600 text-sm"}>{feedback.reason}</div>
          )}
        </div>
      </div>
      <div className={"border-t last:border-none"}></div>
    </Fragment>
  );
};

export default function RequirementsStatus({
  issues,
  isLoading,
  hasSubmitted,
}) {
  if (isLoading) {
    return (
      <ScrollArea className={"h-64 space-y-2 pt-0 pb-3"}>
        <div className={"flex flex-col gap-3"} key={"tmp"}>
          {Array(11)
            .fill(null)
            .map((value, index, array) => {
              return (
                <div
                  key={index}
                  className={
                    "w-full bg-zinc-400 animate-pulse rounded-sm h-5 pe-5"
                  }
                ></div>
              );
            })}
          <div></div>
        </div>
      </ScrollArea>
    );
  }

  if (!hasSubmitted) {
    return (
      <div className={"flex items-center gap-3"}>
        <InfoIcon className={"w-5 h-5  flex-shrink-0"} />
        <span className={"font-medium text-zinc-500"}>
          Press <span className={"text-lime-700"}>Verify</span> or{" "}
          <span className={"text-sky-700"}>Auto-Populate</span> to check status.
        </span>
      </div>
    );
  }

  if (issues.length > 0) {
    return (
      <ScrollArea className={"h-64 space-y-2 pt-0 pb-3"}>
        <div className={"flex flex-col gap-3"} key={"tmp"}>
          {issues.map((issue, idx) => SolverFeedbackToWidget(issue, idx))}
        </div>
      </ScrollArea>
    );
  }

  return (
    <div className={"flex items-center gap-3"}>
      <CheckCircle className={"w-5 h-5 text-green-500 flex-shrink-0"} />
      <span className={"font-medium"}>Requirements Met</span>
    </div>
  );
}
