import {
  Container,
  Box,
  Typography,
  Card,
  CardContent,
  Link,
} from "@mui/material";
import { Grid } from "@mui/material";
import { getJobRolesPerPathway } from "../lib/ict";

export default async function Page() {
  const jobRolesByPathway =
    (await getJobRolesPerPathway())?.filter((p) => p.roles.length > 0) ?? [];
  console.log(jobRolesByPathway);
  return (
    <Container maxWidth="xl" sx={{ marginBottom: 4 }}>
      <Box marginBottom={3}>
        <Typography variant="h3">Discover Job Roles</Typography>
        <Typography maxWidth="sm">
          A pathway may have several job roles associated with it. To start, you
          can select a job role that sounds interesting to you.
        </Typography>
      </Box>
      <Grid container spacing={4}>
        {jobRolesByPathway.map((pathway) => (
          <Card
            key={pathway.pathway_id}
            component={Grid}
            size={{ xs: 12, sm: 6, md: 4, lg: 3 }}
          >
            <CardContent>
              <Typography variant="h6">{pathway.pathway_title}</Typography>
              {pathway.roles.map((role) => (
                <Typography key={role.role_id}>
                  <Link href={"ess/" + role.role_id}>{role.title}</Link>
                </Typography>
              ))}
            </CardContent>
          </Card>
        ))}
      </Grid>
    </Container>
  );
}
