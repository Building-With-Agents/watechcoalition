import ScoreCard from "@/app/ui/components/ScoreCard";
import DeletionFlag from "@/app/ui/components/DeletionFlag";
import {
  getCompanyById,
  getEmployerById,
  searchLocations,
} from "@/app/lib/prisma";
import EmployerTeamMembers from "@/app/ui/components/employerdashboard/EmployerTeamMembers";
import { auth } from "@/auth";
import EmployerRecommendedCandidatesTable from "@/app/ui/components/employerdashboard/EmployerRecommendedCandidatesTable";
import Link from "next/link";
import { Alert, Box, Grid, Stack, Typography } from "@mui/material";
import NewJobFormButton from "@/app/ui/components/jobManagement/NewJobFormButton";
import PillButton from "@/app/ui/components/PillButton";
import { SearchOutlined } from "@mui/icons-material";
import { getCompanyJobListings } from "@/app/lib/joblistings";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";

async function processJobs(
  jobs: JobPostCreationDTO[],
): Promise<JobPostCreationDTO[]> {
  await Promise.all(
    jobs.map(async (job) => {
      const processJobZip = async () => {
        if (job.zip) {
          const results = await searchLocations(job.zip, "zip");
          if (results?.length) {
            job.postalGeoData = results[0];
          }
        }
      };
      const processApplications = async () => {
        await Promise.all(
          job.jobApplications.map(async (application) => {
            if (application.Jobseekers.users.zip) {
              const results = await searchLocations(
                application.Jobseekers.users.zip,
                "zip",
              );
              if (results?.length) {
                application.postalGeoData = results[0];
              }
            }
          }),
        );
      };

      await Promise.all([processJobZip(), processApplications()]);
    }),
  );

  return jobs;
}

export const metadata = {
  title: "My Dashboard",
};

export default async function Page() {
  const session = await auth();
  const proInfo = await getEmployerById(session?.user.employerId ?? "");
  const company = await getCompanyById(proInfo?.company_id ?? "");
  let jobs: JobPostCreationDTO[];
  try {
    jobs = await getCompanyJobListings();
  } catch {
    jobs = [];
  }

  const activeJobs = jobs.reduce(
    (total, job) =>
      total + (job.unpublish_date && job.unpublish_date > new Date() ? 1 : 0),
    0,
  );
  const preScreened = jobs.reduce(
    (total, job) => total + job.jobApplications.length,
    0,
  );
  const jobsWithCandidates = await processJobs(
    jobs.filter((job) => job.jobApplications.length > 0) ?? [],
  );

  if (!proInfo || company == undefined) {
    return (
      <div>
        <h1 className="text-2xl">
          There has been an error finding your info please try logging out and
          logging back in
        </h1>
      </div>
    );
  }
  return (
    <Box sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}>
      <DeletionFlag deletionDate={undefined} />
      <Stack spacing={1}>
        {!session?.user.companyId && (
          <Alert severity="error">
            Some functions may be limited. Please log out and log back in to
            gain full functionality
          </Alert>
        )}
        {!session?.user.employeeIsApproved && (
          <Alert severity="error">
            Employer approval pending. May take up to 24 hours for approval. Log
            out and log back in to update Employer Approval status.
          </Alert>
        )}
      </Stack>
      <Typography variant={"h4"} sx={{ color: "secondary.main", mb: 7 }}>
        Welcome back, {session?.user.firstName}
      </Typography>
      <Grid container direction={"row"}>
        <Box sx={{ mr: 2, display: { xs: "none", md: "flex" } }}>
          <EmployerTeamMembers companyid={company.company_id} />
        </Box>
        <Grid size={"grow"}>
          <Grid
            container
            size={"grow"}
            columnSpacing={4.5}
            rowSpacing={2}
            sx={{ justifyContent: "center", mb: 7 }}
          >
            {session?.user.companyIsApproved &&
              session?.user.employeeIsApproved && (
                <NewJobFormButton
                  company_id={session?.user.companyId ?? null}
                  size="large"
                  sx={{ width: { xs: "100%", sm: "auto" } }}
                />
              )}
            <PillButton
              size="large"
              color="secondary"
              startIcon={<SearchOutlined />}
              href="/services/employers/dashboard/talent-search"
              sx={{ width: { xs: "100%", sm: "auto" } }}
            >
              Search for Candidates
            </PillButton>
          </Grid>
          <Grid container spacing={2} sx={{ justifyContent: "center", mb: 7 }}>
            <Grid size={{ xs: 12, md: 4, xl: 3 }}>
              <Link href="/services/employers/dashboard/jobs">
                <ScoreCard title="Your active jobs" val={activeJobs ?? 0} />
              </Link>
            </Grid>
            <Grid size={{ xs: 12, md: 4, xl: 3 }}>
              <ScoreCard
                title="Pre-screened candidates"
                val={preScreened ?? 0}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 4, xl: 3 }}>
              <Link href="/services/employers/dashboard/savedcandidates">
                <ScoreCard
                  title="Saved candidates"
                  val={proInfo.BookmarkedJobseeker.length}
                />
              </Link>
            </Grid>
          </Grid>
          <Grid container rowSpacing={2} columns={1}>
            <Grid
              container
              spacing={1}
              size={1}
              sx={{ justifyContent: "space-between", mb: 4 }}
            >
              <Typography
                variant="h6"
                color="secondary"
                sx={{ alignSelf: "center" }}
              >
                Recommended pre-screened candidates
              </Typography>
              <PillButton
                color="inherit"
                href="/services/employers/dashboard/talent-search"
                startIcon={<SearchOutlined />}
                sx={{ color: "secondary.main" }}
              >
                Search for Candidates
              </PillButton>
            </Grid>
            <Grid size={1}>
              <EmployerRecommendedCandidatesTable jobs={jobsWithCandidates} />
            </Grid>
            <Grid size={1} sx={{ display: { xs: "flex", md: "none" } }}>
              <EmployerTeamMembers companyid={company.company_id} />
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Box>
  );
}
