import Image from "next/image";
import Step1 from "./StepCard1.png";
import Step2 from "./StepCard2.png";
import Step3 from "./StepCard3.png";
import { Box, Grid, Typography } from "@mui/material";
import PillButton from "../PillButton";

export default async function EmployerSteps() {
  return (
    <Box
      sx={{ backgroundColor: "#EBF1F4", px: { xs: 1, md: 5, lg: 10 }, py: 10 }}
    >
      <Box sx={{ justifyItems: "center" }}>
        <Typography variant="h1" color="secondary" sx={{ fontWeight: 500 }}>
          From Post to Hire.
        </Typography>
        <Typography color="textSecondary" sx={{ pt: 2.5 }}>
          Need talent fast? Get job-ready candidates in 14 days.
        </Typography>
        <Typography color="textSecondary" sx={{ pb: 5 }}>
          Average cost-per-hire (direct + internal) saved: $4,700
        </Typography>
      </Box>
      <Grid
        container
        justifyContent="center"
        alignItems="center"
        sx={{
          gap: { xs: 1.5, md: 3 }, // tighten horizontal spacing
          flexWrap: { xs: "wrap", sm: "nowrap" }, // stack on mobile, one row on sm+
        }}
      >
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <Image
            src={Step1}
            alt="Step 1"
            quality={50}
            style={{ width: 350, height: "auto" }}
          />
        </Box>
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <Image
            src={Step2}
            alt="Step 2"
            quality={50}
            style={{ width: 350, height: "auto" }}
          />
        </Box>
        <Box sx={{ display: "flex", justifyContent: "center" }}>
          <Image
            src={Step3}
            alt="Step 3"
            quality={50}
            style={{ width: 350, height: "auto" }}
          />
        </Box>
      </Grid>

      <Grid container justifyContent="center" sx={{ mt: 5 }}>
        <PillButton href="mailto:susanne.mata@computingforall.org">
          Get In Touch
        </PillButton>
      </Grid>
    </Box>
  );
}
