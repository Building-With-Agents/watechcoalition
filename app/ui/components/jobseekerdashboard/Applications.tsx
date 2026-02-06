import { Grid, Typography } from "@mui/material";
import { JobListingCardViewDTO } from "@/data/dtos/JobListingCardViewDTO";
import PillButton from "../PillButton";
import { JobApplicationsTable } from "../JobApplicationsTable";

export default async function Applications({
  jobs,
}: {
  jobs: JobListingCardViewDTO[] | undefined;
}) {
  if (!jobs) {
    return (
      <>
        <Typography variant="h6" sx={{ color: "secondary.main" }}>
          Application Status
        </Typography>
        <div>No applications found.</div>
      </>
    );
  }

  return (
    <>
      <Grid container rowSpacing={2} columns={1}>
        <Grid
          container
          spacing={1}
          size={1}
          sx={{ justifyContent: "space-between" }}
        >
          <Typography
            variant="h6"
            sx={{ color: "secondary.main", alignSelf: "center" }}
          >
            Application Status
          </Typography>
          <PillButton
            color="inherit"
            href="/services/joblistings"
            sx={{ color: "secondary.main" }}
          >
            Search Jobs
          </PillButton>
        </Grid>
        <Grid size={1}>
          <JobApplicationsTable jobs={jobs} />
        </Grid>
      </Grid>
    </>
  );
}
