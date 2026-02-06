import { Box, Grid, Stack, Typography } from "@mui/material";
import diversePool from "./DiversePool.png";
import employersImg from "./logos.png";
import funnel from "./funnel.svg";
import personCoding from "./PersonCoding.jpg";
import Image from "next/image";
import PillButton from "../PillButton";

export default async function MarketingCards() {
  return (
    <Box sx={{ px: { xs: 1, md: 5, lg: 10 }, py: 10 }}>
      <Typography
        variant="h1"
        color="secondary"
        sx={{ fontWeight: 500, textAlign: "center", pb: 10 }}
      >
        Why Choose Us?
      </Typography>
      <Box sx={{ flexGrow: 1, p: 0 }}>
        <Grid container spacing={5}>
          <Stack component={Grid} size={{ xs: 12, md: 8 }} spacing={5}>
            {/* Education Partner Network */}
            <Grid size={12}>
              <Box
                sx={{
                  backgroundColor: "neutral.100",
                  height: "100%",
                  p: 4,
                  borderRadius: "25px",
                }}
              >
                <Stack
                  direction={{ xs: "column", md: "row" }}
                  sx={{ justifyContent: "space-between" }}
                >
                  <Typography
                    variant="h3"
                    sx={{ fontWeight: 500, alignSelf: "center" }}
                  >
                    Education partner network
                  </Typography>
                  <Box sx={{ width: "450px" }}>
                    <Image src={employersImg} alt="partner logo" />
                  </Box>
                </Stack>
              </Box>
            </Grid>
            {/* Job-ready candidates */}
            <Grid container spacing={5}>
              <Grid size={{ xs: 12, md: 6 }} sx={{ minHeight: "400px" }}>
                <Box
                  sx={{
                    backgroundImage: `url(${personCoding.src})`,
                    backgroundSize: "cover",
                    height: "100%",
                    p: 4,
                    borderRadius: "25px",
                  }}
                >
                  <Typography
                    variant="h3"
                    sx={{ color: "neutral.white", fontWeight: 500 }}
                  >
                    Job-ready, vetted candidates
                  </Typography>
                </Box>
              </Grid>

              {/* Local diverse pool */}
              <Grid size={{ xs: 12, md: 6 }}>
                <Box
                  sx={{
                    backgroundColor: "neutral.100",
                    height: "100%",
                    p: 4,
                    borderRadius: "25px",
                  }}
                >
                  <Typography
                    variant="h3"
                    sx={{ fontWeight: 500, alignSelf: "center" }}
                  >
                    Local & diverse WA talent pool
                  </Typography>
                  <Box sx={{ my: 2.5 }}>
                    <Image
                      src={diversePool}
                      alt="A picture of 7 different candidates"
                    />
                  </Box>
                </Box>
              </Grid>
            </Grid>
          </Stack>

          <Grid container size={{ xs: 12, md: 4 }} spacing={5}>
            {/* Reduced screening time */}
            <Grid size={12}>
              <Stack
                sx={{
                  backgroundColor: "neutral.100",
                  height: "100%",
                  p: 4,
                  borderRadius: "25px",
                  justifyContent: "flex-start",
                  alignItems: "center", // keep the rest centered
                  gap: 1.5,
                }}
              >
                <Typography
                  variant="h3"
                  sx={{
                    fontWeight: 500,
                    alignSelf: "stretch",
                    textAlign: "left",
                    lineHeight: 1.1,
                  }}
                >
                  <Box component="span" display="block">
                    Reduced
                  </Box>
                  <Box component="span" display="block">
                    screening time
                  </Box>
                </Typography>

                <Typography sx={{ fontWeight: 500 }} color="textSecondary">
                  1,000 raw résumés
                </Typography>

                <Box
                  sx={{
                    my: 2.5,
                    flexGrow: 1,
                    width: "100%",
                    position: "relative",
                  }}
                >
                  <Image
                    src={funnel}
                    alt="funnel"
                    fill
                    style={{ objectFit: "contain" }}
                  />
                </Box>

                <Typography sx={{ fontWeight: 500 }}>
                  5 CFA finalists
                </Typography>
              </Stack>
            </Grid>

            {/* $0 placement fees */}
            <Grid size={12}>
              <Box
                sx={{
                  backgroundColor: "neutral.100",
                  height: "100%",
                  p: 4,
                  borderRadius: "25px",
                  display: "flex",
                  alignItems: "center", // vertical center
                  justifyContent: "center", // horizontal center
                  textAlign: "center",
                  minHeight: 200, // optional: ensures enough height to see the centering
                }}
              >
                <Stack spacing={1} alignItems="center">
                  <Typography
                    variant="h1"
                    sx={{ fontWeight: 700, lineHeight: 1 }} // larger $0
                  >
                    $0
                  </Typography>
                  <Typography variant="h4" sx={{ fontWeight: 500 }}>
                    placement fees
                  </Typography>
                </Stack>
              </Box>
            </Grid>
          </Grid>
          {/* Why free */}
          <Grid size={12}>
            <Box
              sx={{
                backgroundColor: "neutral.100",
                height: "100%",
                p: 4,
                borderRadius: "25px",
              }}
            >
              <Grid container direction={{ xs: "column", lg: "row" }}>
                <Stack
                  component={Grid}
                  size={{ xs: 12, lg: 6 }}
                  spacing={{ xs: 1, lg: 5 }}
                >
                  <Typography variant="h3" sx={{ fontWeight: 500 }}>
                    Why is it free for now
                  </Typography>
                  <Box>
                    <PillButton
                      href="/about-us"
                      color="inherit"
                      variant="outlined"
                      sx={{ fontSize: "1.5rem" }}
                    >
                      Learn More
                    </PillButton>
                  </Box>
                </Stack>
                <Grid size={{ xs: 12, lg: 6 }}>
                  <Typography sx={{ fontSize: "1.5rem", mr: 2 }}>
                    Our sourcing service is fully funded by Washington’s Good
                    Jobs Challenge grant, which covers all placement costs as we
                    help place 1,000 tech workers by Sept 2026. After the grant
                    sunsets, CFA will shift to a cost-share model. Until then,
                    employer access is 100% free.
                  </Typography>
                </Grid>
              </Grid>
            </Box>
          </Grid>
        </Grid>
      </Box>
    </Box>
  );
}
