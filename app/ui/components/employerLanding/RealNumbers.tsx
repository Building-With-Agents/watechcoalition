import { Box, Divider, Grid, Stack, Typography } from "@mui/material";

export default async function RealNumbers() {
  return (
    <Box sx={{ my: 10, px: { xs: 1, md: 5, lg: 10 } }}>
      <Typography
        variant="h1"
        color="secondary"
        sx={{ fontWeight: 500, pb: 10 }}
      >
        Real Numbers, Real Talent
      </Typography>
      <Grid container spacing={{ xs: 3, sm: 5, md: 10, lg: 15 }}>
        <Stack
          size={{ xs: 12, md: 4 }}
          component={Grid}
          spacing={5}
          divider={<Divider flexItem />}
        >
          <Typography
            variant="h1"
            color="secondary"
            sx={{ fontWeight: 500, mb: 2.5 }}
          >
            1,400
          </Typography>
          <Box>
            <Typography variant="h3" color="secondary" sx={{ fontWeight: 500 }}>
              Learners
            </Typography>
            <Typography sx={{ fontSize: "1.5rem" }}>
              We have 1440 learners who turned into 780 grads, which results in
              540 job‑ready candidates.
            </Typography>
          </Box>
        </Stack>
        <Stack
          size={{ xs: 12, md: 4 }}
          component={Grid}
          spacing={5}
          divider={<Divider flexItem />}
        >
          <Typography
            variant="h1"
            color="secondary"
            sx={{ fontWeight: 500, mb: 2.5 }}
          >
            150+
          </Typography>
          <Box>
            <Typography variant="h3" color="secondary" sx={{ fontWeight: 500 }}>
              WA Companies
            </Typography>
            <Typography sx={{ fontSize: "1.5rem" }}>
              Hired Coalition candidates
            </Typography>
          </Box>
        </Stack>
        <Stack
          size={{ xs: 12, md: 4 }}
          component={Grid}
          spacing={5}
          divider={<Divider flexItem />}
        >
          <Typography
            variant="h1"
            color="secondary"
            sx={{ fontWeight: 500, mb: 2.5 }}
          >
            9
          </Typography>
          <Box>
            <Typography variant="h3" color="secondary" sx={{ fontWeight: 500 }}>
              Tech Pathways
            </Typography>
            <Typography sx={{ fontSize: "1.5rem" }}>
              Our grads come through Software, Cloud/IT Ops, Cyber, Data, Infra,
              Support, Networks, PM/Prod, and UX/UI training.
            </Typography>
          </Box>
        </Stack>
      </Grid>
    </Box>
  );
}
