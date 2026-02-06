export const dynamic = "force-dynamic";
import { getAllJobPosts } from "@/app/lib/joblistings";
import JobTrackingTable from "@/app/ui/components/careerPrep/JobTrackingTable";
import * as React from "react";

export default async function Page() {
  const jobposts = await getAllJobPosts();
  if (!jobposts) {
    return (
      <main>
        <h1 className="text-2xl">No Job Lisings Found</h1>
      </main>
    );
  }
  return (
    <main className="flex flex-col">
      <h1 className="text-2xl">Job Tracking</h1>
      <JobTrackingTable data={jobposts} />
    </main>
  );
}
