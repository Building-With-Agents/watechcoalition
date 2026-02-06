"use client";

import React, { useState } from "react";
import { Box, Grid, Stack, Tab, Tabs, Typography } from "@mui/material";
import { JobListingCardViewDTO } from "@/data/dtos/JobListingCardViewDTO";
import { JobApplicationsTable } from "../JobApplicationsTable";

interface JobApplicationsProps {
  activeJobs: JobListingCardViewDTO[];
  nonActiveJobs: JobListingCardViewDTO[];
}

export default function MyJobApplications({
  activeJobs,
  nonActiveJobs,
}: JobApplicationsProps) {
  // 0 = Active, 1 = Archive
  const [tabIndex, setTabIndex] = useState(0);

  const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
    setTabIndex(newValue);
  };

  const jobsToDisplay = tabIndex === 0 ? activeJobs : nonActiveJobs;

  return (
    <Stack direction="column" spacing={4}>
      <Typography variant="h3" sx={{ color: "secondary.main" }}>
        Applications
      </Typography>
      <Box sx={{ mb: 2, borderBottom: 1, borderColor: "divider" }}>
        <Tabs
          value={tabIndex}
          onChange={handleTabChange}
          aria-label="Active or Archived Applications"
        >
          <Tab id="tab-0" label="Active" />
          <Tab id="tab-1" label="Archive" />
        </Tabs>
      </Box>

      <Grid container rowSpacing={2} columns={1}>
        <Grid size={12}>
          <JobApplicationsTable jobs={jobsToDisplay} />
        </Grid>
      </Grid>
    </Stack>
  );
}
