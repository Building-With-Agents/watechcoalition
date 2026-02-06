import { getEmployersByCompanyId } from "@/app/lib/prisma";
import { auth } from "@/auth";
import ShareMenu from "../ShareButton";
import { Avatar, Grid, IconButton, Stack, Typography } from "@mui/material";
import { Add } from "@mui/icons-material";

export default async function EmployerTeamMembers(props: {
  companyid: string;
}) {
  const session = await auth();
  const teamates = await getEmployersByCompanyId(props.companyid);
  return (
    <div>
      <Typography
        variant="h5"
        sx={{
          color: "secondary.main",
          justifySelf: { xs: "auto", md: "center" },
        }}
      >
        My team
      </Typography>
      <Grid container spacing={3} direction={{ xs: "row", md: "column" }}>
        <Stack sx={{ alignItems: "center" }}>
          <ShareMenu href={"/signin"}>
            <IconButton sx={{ bgcolor: "primary.light" }}>
              <Add color="secondary" sx={{ width: 40, height: 40 }} />
            </IconButton>
          </ShareMenu>
          <Typography sx={{ color: "secondary.main", mt: 1 }}>
            Invite new teammate
          </Typography>
        </Stack>
        {teamates
          .filter((t) => t.employer_id != session?.user.employerId)
          .map((t) => {
            return (
              <Stack sx={{ alignItems: "center" }} key={t.employer_id}>
                <Avatar
                  src={t.users.photo_url ?? undefined}
                  sx={{ width: 64, height: 64 }}
                />
                <Typography sx={{ color: "secondary.main", mt: 1 }}>
                  {t.users.first_name} {t.users.last_name}
                </Typography>
              </Stack>
            );
          })}
      </Grid>
    </div>
  );
}
