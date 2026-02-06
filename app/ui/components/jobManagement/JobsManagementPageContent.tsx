"use client";

import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import { ArrowBack } from "@mui/icons-material";
import { Box, Typography } from "@mui/material";
import Link from "next/link";
import { useEffect, useState } from "react";
import NewJobFormButton from "./NewJobFormButton";
import JobListingsTable from "./JobListingsTable";
import { useSession } from "next-auth/react";

async function fetchMyJobListings(): Promise<any> {
  const response = await fetch("/api/joblistings/getcompanyjoblistings", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Error fetching jobs");
  }
  return response.json();
}

export default function JobsManagementPageContent() {
  const { data: session } = useSession();
  const [joblistings, setJobListings] = useState<JobPostCreationDTO[]>([]);

  useEffect(() => {
    const fetchJobListings = async () => {
      try {
        const myJobListings = await fetchMyJobListings();
        setJobListings(myJobListings);
      } catch {}
    };
    fetchJobListings();
  }, []);

  const handleJobUpdated = (job: JobPostCreationDTO, action: string) => {
    if (action === "delete") {
      setJobListings((prevJobs) =>
        prevJobs.filter((j) => j.job_posting_id !== job.job_posting_id),
      );
    } else if (action === "update") {
      setJobListings((prevJobs) =>
        prevJobs.map((j) =>
          j.job_posting_id === job.job_posting_id ? job : j,
        ),
      );
    } else if (action === "create") {
      setJobListings((prevJobs) => [...prevJobs, job]);
    }
  };

  return (
    <Box sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}>
      <Link href="/services/employers/dashboard">
        <ArrowBack sx={{ width: "16px", height: "16px" }} /> My Dashboard
      </Link>

      <Typography variant="h3" sx={{ color: "secondary.main", mb: 5 }}>
        Job Management
      </Typography>

      {session?.user?.companyIsApproved &&
        session?.user?.employeeIsApproved && (
          <Box sx={{ mb: 5 }}>
            <NewJobFormButton
              company_id={session?.user.companyId || ""}
              onJobCreated={(newJob: JobPostCreationDTO) =>
                handleJobUpdated(newJob, "create")
              }
            />
          </Box>
        )}

      <Box>
        <JobListingsTable
          company_id={session?.user.companyId || ""}
          jobs={joblistings}
          onJobUpdated={handleJobUpdated}
        />
      </Box>
    </Box>
  );
}
