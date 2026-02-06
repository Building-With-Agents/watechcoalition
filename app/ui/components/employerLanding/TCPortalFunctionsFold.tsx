import Image from "next/image";
import talentSolutionsImage from "./TalentSolutions.jpg";
import { Box, Divider, Grid, Stack, Typography } from "@mui/material";
export default async function TCPortalFunctionsFold() {
  return (
    <Box
      sx={{ px: { xs: 1, md: 5, lg: 10 }, pt: 10, maxWidth: 1720, mx: "auto" }}
    >
      <Typography
        variant="h1"
        color="secondary"
        sx={{
          fontWeight: 500,
          mb: { xs: 3, md: 6 },
          lineHeight: 1.1,
          fontSize: { xs: "2.5rem", md: "3.25rem", lg: "3.75em" },
        }}
      >
        Talent Solutions at a Glance.
      </Typography>
      <Grid spacing={{ sm: 2, md: 10 }} container sx={{ mt: { xs: 0, md: 0 } }}>
        <Stack
          spacing={5}
          component={Grid}
          size={{ sm: 12, md: 6 }}
          divider={<Divider flexItem />}
        >
          <Box>
            <Typography variant="h4" color="secondary">
              Qualified Applicants
            </Typography>
            <Typography color="textSecondary" sx={{ fontSize: "1.5rem" }}>
              No resumes overload—just the top options delivered in ≤ 2 weeks.
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="secondary">
              Skills and Culture Match
            </Typography>
            <Typography color="textSecondary" sx={{ fontSize: "1.5rem" }}>
              Vetted against your exact tech stack & values.
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="secondary">
              Dedicated Partner
            </Typography>
            <Typography color="textSecondary" sx={{ fontSize: "1.5rem" }}>
              We are supporting you at every step tracking progress.
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="secondary">
              Professional Networking
            </Typography>
            <Typography color="textSecondary" sx={{ fontSize: "1.5rem" }}>
              Exclusive access to our network of top-tier employers at virtual
              job fairs & in-person happy hours.
            </Typography>
          </Box>
          <Box>
            <Typography variant="h4" color="secondary">
              Volunteer Mentorship
            </Typography>
            <Typography color="textSecondary" sx={{ fontSize: "1.5rem" }}>
              Speak on panels & workshops. Gain résumé‑worthy leadership
              experience & help career‑switchers break into tech.
            </Typography>
          </Box>
        </Stack>
        <Grid size={{ sm: 12, md: 6 }}>
          <Box
            sx={{
              height: { xs: "400px", md: "fit-content" },
              overflow: "hidden",
              borderRadius: "25px",
            }}
          >
            <Image
              src={talentSolutionsImage}
              alt=""
              style={{ height: "auto" }}
            />
          </Box>
        </Grid>
      </Grid>
    </Box>
  );
}
