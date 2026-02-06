import ApplyToJobButton from "@/app/ui/components/jobPostings/ApplyToJobButton";
import DeleteJobPostingButton from "@/app/ui/components/jobPostings/DeleteJobPostingButton";
import Skills from "@/app/ui/components/Skills";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { Role } from "@/data/dtos/UserInfoDTO";
import { auth } from "@/auth";
import { Alert, Box, Grid, Stack, Tab, Tabs, Typography } from "@mui/material";
import { Circle } from "@mui/icons-material";
import "quill/dist/quill.snow.css";
import BookmarkWithText from "../BookmarkWithText";

interface Props {
  joblisting: any;
  params: any;
}

export default async function JobPostingPage({ joblisting, params }: Props) {
  const session = await auth();

  const job_title: string = joblisting?.job_title ?? "";
  const employment_type: string = joblisting?.employment_type ?? "";
  const earn_and_learn_type: string = joblisting?.earn_and_learn_type ?? "";
  const company_name: string = joblisting?.companies.company_name ?? "";
  const skills: SkillDTO[] = joblisting?.skills ?? [];
  const salary_range: string = joblisting?.salary_range ?? "";
  const description: string = joblisting?.job_description ?? "";
  const location: string = joblisting?.location;
  const city: string = joblisting?.company_addresses?.locationData.city;
  const state: string = joblisting?.company_addresses?.locationData.stateCode;
  const isJobseeker = session?.user.roles.includes(Role.JOBSEEKER);

  return (
    <>
      {joblisting.career_services_offered && (
        <Grid container sx={{ mb: 2, mx: { xs: 3, md: 6.25 } }}>
          <Alert color="info">Employer Partner Jobs</Alert>
        </Grid>
      )}
      <Stack
        direction={"column"}
        spacing={4}
        sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}
      >
        <Grid container direction={{ xs: "column", sm: "row" }}>
          <Grid size="grow">
            <Stack direction={"row"} spacing={2} sx={{ alignItems: "center" }}>
              <Typography variant="h3">{job_title}</Typography>
              {session &&
                joblisting &&
                session.user.companyId === joblisting.company_id && (
                  <DeleteJobPostingButton id={params.id} />
                )}
            </Stack>
            <Typography variant="h5">{company_name}</Typography>
          </Grid>
          <Stack
            direction={{ xs: "column", lg: "row" }}
            spacing={2}
            sx={{ display: { xs: "none", sm: "flex" } }}
          >
            {isJobseeker && (
              <div>
                <BookmarkWithText
                  bookmarked={joblisting.isBookmarked}
                  addUrl={
                    "/api/joblistings/bookmark/add/" + joblisting.job_posting_id
                  }
                  removeUrl={
                    "/api/joblistings/bookmark/remove/" +
                    joblisting.job_posting_id
                  }
                />
              </div>
            )}
            {(!session?.user || isJobseeker) && (
              <div>
                <ApplyToJobButton
                  id={params.id}
                  job_post_url={joblisting.job_post_url}
                  appliedStatus={joblisting.jobStatus}
                  unPublishDate={joblisting.unpublish_date}
                />
              </div>
            )}
          </Stack>
        </Grid>
        <Stack
          direction={{ xs: "column", sm: "row" }}
          columnGap={2}
          rowGap={0.5}
          sx={{ alignItems: { sm: "center" }, textTransform: "capitalize" }}
        >
          <Typography>{location}</Typography>
          <Circle sx={{ fontSize: 8, display: { xs: "none", sm: "inline" } }} />
          <Typography>
            {employment_type === "Earn and Learn"
              ? earn_and_learn_type
              : employment_type}
          </Typography>
          <Circle sx={{ fontSize: 8, display: { xs: "none", sm: "inline" } }} />
          <Typography>
            {city}, {state}
          </Typography>
          <Circle sx={{ fontSize: 8, display: { xs: "none", sm: "inline" } }} />
          <Typography>
            {joblisting.is_paid ? salary_range : "unpaid"}
          </Typography>
          <Circle sx={{ fontSize: 8, display: { xs: "none", sm: "inline" } }} />
          <Typography>
            Deadline:{" "}
            {joblisting?.unpublish_date
              ? new Date(joblisting.unpublish_date).toLocaleDateString(
                  "en-us",
                  {
                    month: "numeric",
                    day: "numeric",
                    year: "numeric",
                  },
                )
              : "N/A"}
          </Typography>
        </Stack>
        <Stack rowGap={2} direction="column" sx={{ display: { sm: "none" } }}>
          {isJobseeker && (
            <Box>
              <BookmarkWithText
                bookmarked={joblisting.isBookmarked}
                addUrl={
                  "/api/joblistings/bookmark/add/" + joblisting.job_posting_id
                }
                removeUrl={
                  "/api/joblistings/bookmark/remove/" +
                  joblisting.job_posting_id
                }
              />
            </Box>
          )}
          {(!session?.user || isJobseeker) && (
            <div>
              <ApplyToJobButton
                id={params.id}
                job_post_url={joblisting.job_post_url}
                appliedStatus={joblisting.jobStatus}
                unPublishDate={joblisting.unpublish_date}
              />
            </div>
          )}
        </Stack>
        <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
          <Tabs value={0} aria-label="Details of job">
            <Tab id="tab-0" label="Details" />
          </Tabs>
        </Box>

        {/* Company Information */}
        {(joblisting?.companies.about_us ||
          joblisting?.companies.company_mission ||
          joblisting?.companies.company_vision ||
          description) && (
          <Stack rowGap={2}>
            {joblisting?.companies.about_us && (
              <>
                <Typography sx={{ fontWeight: "bold" }}>Our Company</Typography>
                <p>{joblisting?.companies.about_us}</p>
              </>
            )}
            {joblisting?.companies.company_mission && (
              <>
                <Typography sx={{ fontWeight: "bold" }}>Our Mission</Typography>
                <p>{joblisting?.companies.company_mission}</p>
              </>
            )}
            {joblisting?.companies.company_vision && (
              <>
                <Typography sx={{ fontWeight: "bold" }}>Our Vision</Typography>
                <p>{joblisting?.companies.company_vision}</p>
              </>
            )}
            <>
              <Typography sx={{ fontWeight: "bold" }}>Description</Typography>
              <div
                dangerouslySetInnerHTML={{ __html: description }}
                className="ql-editor"
              />
            </>
          </Stack>
        )}

        {/* Skills */}
        {skills.length > 0 && (
          <div>
            <p className="font-semibold text-gray-700">Skills:</p>
            <div className="mt-2 flex grow text-sm tablet:text-base">
              <Skills
                skillsList={skills}
                maxNumSkills={11}
                jobseekerID={undefined}
              />
            </div>
          </div>
        )}
      </Stack>
    </>
  );
}
