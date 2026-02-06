export const dynamic = "force-dynamic";
import ICTRecommendationTable from "@/app/ui/components/careerPrep/ICTRecommendationTable";
import { Container, Typography } from "@mui/material";
import * as React from "react";

export default async function Page() {
  return (
    <Container maxWidth={false}>
      <Typography variant="h5" sx={{ mb: 2 }}>
        ICT Job Role Recommendations
      </Typography>
      <ICTRecommendationTable />
    </Container>
  );
}
