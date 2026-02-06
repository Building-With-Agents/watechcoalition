import { getJobRole } from "@/app/lib/ict";
import EmployerFeedbackForm from "@/app/ui/components/feedback-forms/EmployerFeedbackForm";
import RecommendedJobSeekersTable from "@/app/ui/components/feedback-forms/RecommendedJobSeekersTable";
import { auth } from "@/auth";
import { ExpandMore } from "@mui/icons-material";
import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemText,
  Grid,
  Stack,
  Accordion,
  AccordionDetails,
  AccordionSummary,
} from "@mui/material";

export default async function Page(props: {
  params: Promise<{ jobrole: string }>;
}) {
  const [session, params] = await Promise.all([auth(), props.params]);
  const jobRole = await getJobRole(params.jobrole);
  const employer = session?.user.employeeIsApproved;

  if (!jobRole) {
    return (
      <Container maxWidth="xl">
        <Box mb={2}>
          <Button sx={{ my: 2 }} variant="contained" href="/ess">
            See other Job Roles
          </Button>
          <Typography>No Job Role Found</Typography>
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl">
      <Box mb={2}>
        <Button sx={{ my: 2 }} variant="contained" href="/ess">
          See other Job Roles
        </Button>
        <Typography
          variant="h2"
          component="h2"
          fontWeight="bold"
          sx={{ wordBreak: "break-word" }}
        >
          {jobRole?.title}
        </Typography>
        {employer && (
          <>
            <Accordion sx={{ p: 2, mt: 2 }}>
              <AccordionSummary
                expandIcon={<ExpandMore />}
                aria-controls="employer-feedback-content"
                id="employer-feedback-header"
              >
                <Typography variant="h5" fontWeight="bold">
                  Employer Feedback Form
                </Typography>
                <Typography sx={{ alignContent: "center", ml: 2 }}>
                  Help us find you better job matches
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <EmployerFeedbackForm jobroleId={params.jobrole} />
              </AccordionDetails>
            </Accordion>
            <Accordion sx={{ p: 2, mb: 2 }}>
              <AccordionSummary
                expandIcon={<ExpandMore />}
                aria-controls="job-seeker-matches-content"
                id="job-seeker-matches-header"
              >
                <Typography variant="h5" fontWeight="bold">
                  Job Seeker Matches
                </Typography>
                <Typography sx={{ alignContent: "center", ml: 2 }}>
                  Check out the candidates best matched for this role
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <RecommendedJobSeekersTable jobRoleId={params.jobrole} />
              </AccordionDetails>
            </Accordion>
          </>
        )}

        <Card sx={{ p: 2, mb: 2, mt: 2 }}>
          <CardContent component={Stack} spacing={2}>
            <Box>
              <Typography variant="h5" fontWeight="bold">
                Description
              </Typography>
              <List disablePadding>
                {jobRole.jobDescription
                  ?.split(".")
                  .filter((point: string) => point.trim() !== "")
                  .map((point: string, index: number) => (
                    <ListItem disableGutters key={index}>
                      <ListItemText>{point.trim()}</ListItemText>
                    </ListItem>
                  ))}
              </List>
            </Box>

            <Typography variant="h5" fontWeight="bold">
              AI Impact
            </Typography>
            <Typography>{jobRole.aiImpact}</Typography>

            <Typography variant="h5" fontWeight="bold">
              AI Transformation Potential
            </Typography>
            <Typography>{jobRole.aiTransformation}</Typography>
          </CardContent>
        </Card>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: "grow" }}>
            <Card>
              <CardContent>
                <Typography variant="h5" fontWeight="bold">
                  Key Insights
                </Typography>
                <List disablePadding>
                  {jobRole.keyInsights
                    ?.split("~")
                    .filter((point: string) => point.trim() !== "")
                    .map((point: string, index: number) => (
                      <ListItem disableGutters key={index}>
                        <ListItemText>{point.trim()}</ListItemText>
                      </ListItem>
                    ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: "grow" }}>
            <Card>
              <CardContent>
                <Typography variant="h5" fontWeight="bold">
                  Principal Tasks
                </Typography>
                <List disablePadding>
                  {jobRole.principalTasks
                    ?.split("~")
                    .filter((point: string) => point.trim() !== "")
                    .map((point: string, index: number) => (
                      <ListItem disableGutters key={index}>
                        <ListItemText>{point.trim()}</ListItemText>
                      </ListItem>
                    ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, md: "grow" }}>
            <Card>
              <CardContent>
                <Typography variant="h5" fontWeight="bold">
                  Principal Skills
                </Typography>
                <List disablePadding>
                  {jobRole.principalSkills
                    ?.split("~")
                    .filter((point: string) => point.trim() !== "")
                    .map((point: string, index: number) => (
                      <ListItem disableGutters key={index}>
                        <ListItemText>{point.trim()}</ListItemText>
                      </ListItem>
                    ))}
                </List>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Box>
    </Container>
  );
}
