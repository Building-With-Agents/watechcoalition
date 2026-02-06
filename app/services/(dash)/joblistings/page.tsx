import { Suspense } from "react";
import JobListingsContent from "@/app/ui/components/jobPostings/JobListingsContent";

export default function Page() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <JobListingsContent />
    </Suspense>
  );
}
