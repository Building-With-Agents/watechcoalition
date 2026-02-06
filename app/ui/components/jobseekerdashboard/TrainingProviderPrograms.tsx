import { Grid, Stack, Typography } from "@mui/material";
import { ReadEduProviderProgramCardDTO } from "@/app/lib/eduProviders";
import TrainingProgramCard from "@/app/ui/components/career/TrainingProgramCard";
import PillButton from "../PillButton";
import React from "react";

export default async function TrainingProviderPrograms({
  programs,
}: {
  programs: ReadEduProviderProgramCardDTO[];
}) {
  return (
    <Stack direction={"column"} gap={2}>
      <Grid gap={1} container sx={{ justifyContent: "space-between" }}>
        <Typography
          variant="h6"
          sx={{
            color: "secondary.main",
            alignSelf: "center",
          }}
        >
          Coalition Training Provider Programs
        </Typography>
        <PillButton
          color="inherit"
          href="/services/training-providers"
          sx={{
            color: "secondary.main",
          }}
        >
          See More
        </PillButton>
      </Grid>
      <p>
        Kickstart your career with practical, industry-relevant training. These
        partner programs provide the skills, mentorship, and credentials
        essential for success in your tech field.
      </p>
      <Grid container gap={2}>
        {programs.map(function (program) {
          return (
            <React.Fragment key={program.programId}>
              {TrainingProgramCard(program)}
            </React.Fragment>
          );
        })}
      </Grid>
    </Stack>
  );
}
