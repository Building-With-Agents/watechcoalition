"use client";
import { JobStatus } from "@/app/lib/jobseekerJobTracking";
import { useRouter } from "next/navigation";

export default function JobStatusDropDown(props: {
  currentJobStatus: JobStatus;
  jobAppId: string;
}) {
  const router = useRouter();
  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const newStatus = event.target.value as JobStatus;
    console.log("change detected: ", props.jobAppId);
    fetch("/api/admin/career-prep/update-job-status", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        joinTableId: props.jobAppId,
        newJobStatus: newStatus,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          event.target.value = props.currentJobStatus;
          throw new Error("Failed to update status");
        }
        return response.json();
      })
      .then((data) => {
        console.log("Status updated successfully:", data);
        router.refresh();
      })
      .catch((error) => {
        console.error("Error updating status:", error);
      });
  };
  return (
    <select onChange={handleChange} defaultValue={props.currentJobStatus}>
      {props.currentJobStatus == undefined ? <option>Unknown</option> : ""}
      {Object.values(JobStatus).map((stat) => (
        <option
          key={stat}
          value={stat}
          //   selected={stat == props.careerPrepEnrollmentStatus}
        >
          {stat}
        </option>
      ))}
    </select>
  );
}
