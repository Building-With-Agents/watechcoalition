import { auth } from "@/auth";
import {
  getPoolWithSession,
  getCareerPrepAssementStatus,
} from "@/app/lib/jobseeker";
import { getJobSeekerEmployerView } from "@/app/lib/prisma";
import { getJobSeekerAppliedJobs } from "@/app/lib/joblistings";
import { getCareerPrepStatus } from "@/app/lib/admin/careerPrep";
import { Stack, Typography } from "@mui/material";
import Applications from "@/app/ui/components/jobseekerdashboard/Applications";
import PillButton from "@/app/ui/components/PillButton";
import AnnouncementSpace from "@/app/ui/components/jobseekerdashboard/AnnouncementSpace";

export const metadata = {
  title: "My Dashboard",
};

export default async function Page() {
  const session = await auth();
  const pool = await getPoolWithSession(); // eslint-disable-line @typescript-eslint/no-unused-vars

  const [AssementInfo, jobseekerData, appliedJobs] = await Promise.all([
    getCareerPrepAssementStatus(),
    getJobSeekerEmployerView(session?.user.jobseekerId || ""),
    getJobSeekerAppliedJobs(),
    getCareerPrepStatus(session?.user.jobseekerId ?? ""),
  ]);

  // let providerPrograms;
  if (jobseekerData && jobseekerData.pathways) {
    // providerPrograms = (
    //   await getProviderProgramCardView(
    //     jobseekerData?.pathways?.pathway_title || "",
    //   )
    // ).splice(0, 3);
  }
  const slicedAppliedJobs = appliedJobs?.slice(0, 3);

  const hasTakenTest = // eslint-disable-line @typescript-eslint/no-unused-vars
    AssementInfo != undefined && AssementInfo.CareerPrepAssessment.length > 0;

  return (
    <Stack
      direction={"column"}
      spacing={4}
      sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}
    >
      {/*hasTakenTest ? (
        ''
      ) : (
        <CallTOActionBanner pool={pool?.assignedPool as PoolCategories} />
      )*/}
      <Stack
        direction={"row"}
        spacing={2}
        sx={{
          mb: "0.25rem",
          width: "100%",
          justifyContent: "center",
          alignItems: "center",
          alignSelf: "stretch",
        }}
      >
        <PillButton color="secondary">Dashboard</PillButton>
        <Typography
          variant="h4"
          sx={{ fontSize: "24px", textAlign: "center", fontWeight: 400 }}
        >
          |
        </Typography>
        <PillButton
          color="inherit"
          href={"/services/jobseekers/" + session?.user.jobseekerId}
          sx={{
            color: "secondary.main",
          }}
        >
          Showcase
        </PillButton>
      </Stack>
      <Typography variant={"h4"} sx={{ color: "secondary.main" }}>
        Welcome back, {session?.user.firstName}
      </Typography>
      <AnnouncementSpace />
      <Applications jobs={slicedAppliedJobs} />
      {/*<EventsList*/}
      {/*  headerText={"My Events"}*/}
      {/*  showOnlyRegisteredEvents={true}*/}
      {/*  showMeetingLinks={true}*/}
      {/*></EventsList>*/}
      {/*{providerPrograms && (*/}
      {/*  <TrainingProviderPrograms programs={providerPrograms} />*/}
      {/*)}*/}
    </Stack>
  );
}
