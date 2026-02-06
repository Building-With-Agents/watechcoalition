import { getJobSeekerAppliedJobs } from "@/app/lib/joblistings";
import { JobStatus } from "@/app/lib/jobseekerJobTracking";
import MyJobApplications from "@/app/ui/components/jobPostings/MyJobApplications";
import { JobListingCardViewDTO } from "@/data/dtos/JobListingCardViewDTO";
import { ArrowBack } from "@mui/icons-material";
import { Box } from "@mui/material";
import Link from "next/link";

export default async function Page() {
  const myAppliedJobs: JobListingCardViewDTO[] | undefined =
    await getJobSeekerAppliedJobs();

  if (!myAppliedJobs || myAppliedJobs.length === 0) {
    return (
      <div>
        <p>
          No Applications Found:{" "}
          <Link href="/services/joblistings" className="LINK">
            Find Job Listings here
          </Link>
        </p>
      </div>
    );
  }

  const excludedStatuses = [
    JobStatus.NoResponse,
    JobStatus.IWithdrew,
    JobStatus.NotSelected,
  ];
  const activeJobs = myAppliedJobs.filter(
    (job) => !excludedStatuses.includes(job.jobStatus as JobStatus),
  );
  const nonActiveJobs = myAppliedJobs.filter((job) =>
    excludedStatuses.includes(job.jobStatus as JobStatus),
  );

  return (
    <Box sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}>
      <Link href="/services/jobseekers/dashboard">
        <ArrowBack sx={{ width: "16px", height: "16px" }} /> My Dashboard
      </Link>
      <MyJobApplications
        activeJobs={activeJobs}
        nonActiveJobs={nonActiveJobs}
      />
    </Box>
  );
}
