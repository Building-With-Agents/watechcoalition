import Avatar from "@/app/ui/components/Avatar";
import Skills from "@/app/ui/components/Skills";
import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";
import DeletionFlag from "@/app/ui/components/DeletionFlag";
import EditIcon from "@mui/icons-material/Edit";
import {
  Box,
  Card,
  Chip,
  Container,
  Divider,
  Grid,
  IconButton,
  Link,
  Stack,
  Typography,
} from "@mui/material";
import { Role } from "@/data/dtos/UserInfoDTO";
import PillButton from "@/app/ui/components/PillButton";
import { getJobSeekerEmployerView } from "@/app/lib/prisma";
import { getResumeUrl } from "@/app/lib/services/azureBlobService";
import { auth } from "@/auth";
import { Download } from "@mui/icons-material";
import OgImage from "@/app/ui/components/OgImage";

const monthNames = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

export default async function Page(props: { params: Promise<{ id: string }> }) {
  const [params, session] = await Promise.all([props.params, auth()]);
  const jobseeker = await getJobSeekerEmployerView(params.id);
  const employmentTypesSought = (jobseeker?.employment_type_sought ?? "")
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  const isOwnProfile = session?.user.jobseekerId === params.id;
  let videoID = null;
  let resumeUrl = null;

  if (jobseeker?.video_url) {
    const parsedUrl = new URL(jobseeker?.video_url);
    if (parsedUrl.hostname === "youtu.be") {
      videoID = parsedUrl.pathname.slice(1);
    } else if (
      parsedUrl.hostname === "www.youtube.com" ||
      parsedUrl.hostname === "youtube.com"
    ) {
      videoID = new URLSearchParams(parsedUrl.search).get("v") ?? "";
    }
  }

  if (
    session?.user.employeeIsApproved ||
    isOwnProfile ||
    session?.user.roles.includes(Role.ADMIN) ||
    session?.user.roles.includes(Role.CASE_MANAGER)
  ) {
    if (jobseeker) resumeUrl = await getResumeUrl(jobseeker?.users.id);
  }

  return (
    <Container disableGutters maxWidth="xl">
      <Stack spacing={4} sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}>
        <DeletionFlag deletionDate={undefined} />
        {isOwnProfile && (
          <Stack
            direction={"row"}
            gap={2}
            sx={{
              mb: 2,
              width: "100%",
              justifyContent: "center",
              alignItems: "center",
              alignSelf: "stretch",
            }}
          >
            <PillButton
              color="inherit"
              href={"/services/jobseekers/dashboard"}
              sx={{ color: "secondary.main" }}
            >
              Dashboard
            </PillButton>
            <Typography
              variant="h4"
              sx={{ fontSize: "24px", textAlign: "center", fontWeight: 400 }}
            >
              |
            </Typography>
            <PillButton color="secondary">Showcase</PillButton>
          </Stack>
        )}
        <Card sx={{ p: 2 }}>
          <Stack
            direction={{ xs: "column", md: "row" }}
            columnGap={5}
            rowGap={2}
            sx={{ alignItems: { xs: "center", md: "normal" } }}
          >
            <Avatar
              imgsrc={jobseeker?.users.photo_url ?? undefined}
              scale={1.75}
            />
            <Stack
              direction={"column"}
              sx={{ alignItems: { xs: "center", md: "normal" } }}
            >
              {jobseeker?.users.first_name && (
                <Typography variant="h4">
                  {jobseeker?.users.first_name +
                    " " +
                    jobseeker?.users.last_name}
                </Typography>
              )}
              <Typography variant="h6">
                {jobseeker?.users.locationData?.city},{" "}
                {jobseeker?.users.locationData?.stateCode}
              </Typography>
              {jobseeker?.linkedin_url && (
                <Link
                  href={
                    "https://www.linkedin.com" +
                    jobseeker.linkedin_url
                      .toLowerCase()
                      .split("linkedin.com")[1]
                  }
                  target="_blank"
                  sx={{ wordBreak: "break-word" }}
                >
                  {"https://www.linkedin.com" +
                    jobseeker.linkedin_url
                      .toLowerCase()
                      .split("linkedin.com")[1]}
                </Link>
              )}
              {jobseeker?.portfolio_url && (
                <Link
                  href={jobseeker?.portfolio_url}
                  target="_blank"
                  sx={{ wordBreak: "break-word" }}
                >
                  {jobseeker?.portfolio_url}
                </Link>
              )}
            </Stack>
            {resumeUrl ? (
              <Box sx={{ ml: { md: "auto" } }}>
                <PillButton
                  href={resumeUrl}
                  target="_blank"
                  startIcon={<Download />}
                  color="inherit"
                  sx={{ color: "secondary.main" }}
                >
                  Download Resume
                </PillButton>
              </Box>
            ) : (
              ""
            )}
          </Stack>
          <Divider variant="middle" sx={{ m: 1.5 }} />
          <Stack direction={{ xs: "column", sm: "row" }}>
            <Stack spacing={1} sx={{ p: 2, width: { xs: "100%", sm: "50%" } }}>
              <Typography>Interested in</Typography>
              <Box>
                {employmentTypesSought.length > 0 ? (
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    {employmentTypesSought.map((label) => (
                      <Chip
                        key={label}
                        variant="outlined"
                        color="primary"
                        label={label}
                      />
                    ))}
                  </Stack>
                ) : (
                  <Chip variant="outlined" color="default" label="None" />
                )}
              </Box>
            </Stack>
            <Divider
              variant="middle"
              sx={{
                display: { xs: "block", sm: "none" },
                my: 1.5,
              }}
            />
            <Divider
              orientation="vertical"
              flexItem
              sx={{
                display: { xs: "none", sm: "block" },
              }}
            />
            <Stack spacing={1} sx={{ p: 2, width: { xs: "100%", sm: "50%" } }}>
              <Typography>Tech Pathway</Typography>
              <Box>
                <Chip
                  variant="outlined"
                  color="primary"
                  label={jobseeker?.pathways?.pathway_title}
                />
              </Box>
            </Stack>
          </Stack>
        </Card>
        {/* About Me */}
        <Box>
          <Grid
            container
            columnSpacing={4}
            rowSpacing={2}
            direction={{ xs: "column-reverse", md: "row" }}
          >
            <Grid size={{ xs: 12, md: "grow" }}>
              <Card sx={{ p: 2 }}>
                <Stack
                  direction={"row"}
                  sx={{ justifyContent: "space-between" }}
                >
                  <Typography variant="h5">About Me</Typography>
                  {isOwnProfile && (
                    <IconButton href="/edit-profile/jobseeker/preferences">
                      <EditIcon />
                    </IconButton>
                  )}
                </Stack>
                <Typography>{jobseeker?.intro_headline}</Typography>
              </Card>
            </Grid>
            <Grid container size={{ xs: 12, md: "grow" }}>
              {videoID && (
                <iframe
                  className="aspect-video min-w-[200px]"
                  src={`https://www.youtube.com/embed/${videoID}?autoplay=0`}
                  title="YouTube video player"
                  allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture; web-share"
                  referrerPolicy="strict-origin-when-cross-origin"
                  allowFullScreen
                  style={{ width: "100%" }}
                ></iframe>
              )}
            </Grid>
          </Grid>
        </Box>
        {/* Technical Skills */}
        {jobseeker?.jobseeker_has_skills &&
          jobseeker?.jobseeker_has_skills.length > 0 && (
            <Stack spacing={1} sx={{ p: 2 }}>
              <Typography variant="h5">Top Technical Skills</Typography>
              <Skills
                skillsList={jobseeker?.jobseeker_has_skills.map(
                  (item: JobseekerSkillDTO) => item.skills,
                )}
                jobseekerID={jobseeker?.jobseeker_id}
                maxNumSkills={0}
              />
            </Stack>
          )}
        <Box>
          <Grid container spacing={4}>
            <Stack component={Grid} size={{ xs: 12, md: 4 }} spacing={2}>
              {/* Education */}
              {jobseeker?.jobseeker_education &&
                jobseeker?.jobseeker_education.length > 0 && (
                  <Card sx={{ p: 2 }}>
                    <Stack
                      direction={"row"}
                      sx={{ justifyContent: "space-between" }}
                    >
                      <Typography variant="h5">Education</Typography>
                      {isOwnProfile && (
                        <IconButton href="/edit-profile/jobseeker/education">
                          <EditIcon />
                        </IconButton>
                      )}
                    </Stack>
                    {jobseeker?.jobseeker_education.map((education) => (
                      <Box
                        key={education.id}
                        sx={{
                          position: "relative",
                          pl: 2,
                          "&::before": {
                            content: '""',
                            position: "absolute",
                            top: 16,
                            left: 0,
                            bottom: 0,
                            borderLeft: "2px solid",
                            borderColor: "primary.main",
                          },
                          "&::after": {
                            content: '""',
                            position: "absolute",
                            top: 8,
                            left: -6.5,
                            width: 15,
                            height: 15,
                            borderRadius: "50%",
                            backgroundColor: "primary.main",
                          },
                        }}
                      >
                        <Typography variant="h6">
                          {education.eduProviders.name}
                        </Typography>
                        <Typography>
                          {education?.program?.title} | {education.degreeType}
                        </Typography>
                        <Typography className="text-xs">
                          {monthNames[new Date(education.startDate).getMonth()]}{" "}
                          {new Date(education.startDate).getFullYear()} -{" "}
                          {monthNames[new Date(education.gradDate).getMonth()]}{" "}
                          {new Date(education.gradDate).getFullYear()}
                        </Typography>
                      </Box>
                    ))}
                  </Card>
                )}
              {/* Certificates */}
              {jobseeker?.certificates &&
                jobseeker?.certificates.length > 0 && (
                  <Card sx={{ p: 2 }}>
                    <Stack
                      direction={"row"}
                      sx={{ justifyContent: "space-between" }}
                    >
                      <Typography variant="h5">
                        Licenses &amp; Certifications
                      </Typography>
                      {isOwnProfile && (
                        <IconButton href="/edit-profile/jobseeker/education">
                          <EditIcon />
                        </IconButton>
                      )}
                    </Stack>
                    {jobseeker?.certificates.map((certificate) => (
                      <Box
                        key={certificate.certId}
                        sx={{
                          position: "relative",
                          pl: 2,
                          "&::before": {
                            content: '""',
                            position: "absolute",
                            top: 16,
                            left: 0,
                            bottom: 0,
                            borderLeft: "2px solid",
                            borderColor: "primary.main",
                          },
                          "&::after": {
                            content: '""',
                            position: "absolute",
                            top: 8,
                            left: -6.5,
                            width: 15,
                            height: 15,
                            borderRadius: "50%",
                            backgroundColor: "primary.main",
                          },
                        }}
                      >
                        <Typography
                          variant="h6"
                          sx={{ fontWeight: "bold", fontSize: "1.2rem" }}
                        >
                          {certificate.name}
                        </Typography>
                        {certificate.issueDate && (
                          <Typography className="text-xs">
                            {monthNames[certificate.issueDate.getMonth()]}{" "}
                            {certificate.issueDate.getFullYear()} -{" "}
                            {certificate.expiryDate
                              ? monthNames[certificate.expiryDate.getMonth()] +
                                " " +
                                certificate.expiryDate.getFullYear()
                              : "Present"}
                          </Typography>
                        )}
                        {certificate.credentialUrl ? (
                          <Link
                            sx={{ wordBreak: "break-all" }}
                            target="_blank"
                            href={certificate.credentialUrl}
                          >
                            {certificate.credentialUrl}
                          </Link>
                        ) : (
                          ""
                        )}
                        <p>{certificate.description}</p>
                      </Box>
                    ))}
                  </Card>
                )}
            </Stack>
            <Stack component={Grid} size={{ xs: 12, md: 8 }} spacing={2}>
              {/* Projects */}
              {jobseeker?.project_experiences &&
                jobseeker?.project_experiences.length > 0 && (
                  <Card sx={{ p: 2 }}>
                    <Stack
                      direction={"row"}
                      sx={{ justifyContent: "space-between" }}
                    >
                      <Typography variant="h5" sx={{ mb: 1 }}>
                        Projects
                      </Typography>
                      {isOwnProfile && (
                        <IconButton href="/edit-profile/jobseeker/education">
                          <EditIcon />
                        </IconButton>
                      )}
                    </Stack>
                    <Stack
                      spacing={2}
                      sx={{ pl: 2 }}
                      divider={<Divider sx={{ my: 2 }} />}
                    >
                      {jobseeker.project_experiences.map((experience) => (
                        <Box key={experience.projectId}>
                          {/* Desktop view */}
                          <Box sx={{ display: { xs: "none", md: "block" } }}>
                            <Grid container spacing={4}>
                              {experience.repoUrl && (
                                <Grid size={{ xs: 12, md: 5 }}>
                                  <OgImage siteUrl={experience.repoUrl} />
                                </Grid>
                              )}
                              <Grid size="grow">
                                <Typography variant="h6">
                                  {experience.projTitle}
                                </Typography>
                                <Typography variant="subtitle2">
                                  {
                                    monthNames[
                                      new Date(experience.startDate).getMonth()
                                    ]
                                  }{" "}
                                  {new Date(experience.startDate).getFullYear()}{" "}
                                  -{" "}
                                  {experience.completionDate
                                    ? monthNames[
                                        new Date(
                                          experience.completionDate,
                                        ).getMonth()
                                      ] +
                                      " " +
                                      new Date(
                                        experience.completionDate,
                                      ).getFullYear()
                                    : "Present"}
                                </Typography>
                                {experience.repoUrl ? (
                                  <Link
                                    sx={{ wordBreak: "break-all" }}
                                    target="_blank"
                                    href={experience.repoUrl}
                                  >
                                    {experience.repoUrl}
                                  </Link>
                                ) : (
                                  ""
                                )}
                                <Typography
                                  variant="subtitle1"
                                  sx={{ fontWeight: "bold" }}
                                >
                                  Skills Demonstrated
                                </Typography>
                                <Skills
                                  skillsList={experience.project_has_skills.map(
                                    (item: JobseekerSkillDTO) => item.skills,
                                  )}
                                  maxNumSkills={0}
                                  color="default"
                                  key={experience.projectId + "skills"}
                                />
                              </Grid>
                            </Grid>
                            <Typography
                              variant="subtitle1"
                              sx={{ fontWeight: "bold" }}
                            >
                              Description
                            </Typography>
                            <Typography>
                              {experience.problemSolvedDescription}
                            </Typography>
                          </Box>
                          {/* Mobile view */}
                          <Box sx={{ display: { xs: "block", md: "none" } }}>
                            <Stack>
                              <Typography variant="h6" sx={{ mb: 1 }}>
                                {experience.projTitle}
                              </Typography>
                              <Typography variant="subtitle2">
                                {
                                  monthNames[
                                    new Date(experience.startDate).getMonth()
                                  ]
                                }{" "}
                                {new Date(experience.startDate).getFullYear()} -{" "}
                                {experience.completionDate
                                  ? monthNames[
                                      new Date(
                                        experience.completionDate,
                                      ).getMonth()
                                    ] +
                                    " " +
                                    new Date(
                                      experience.completionDate,
                                    ).getFullYear()
                                  : "Present"}
                              </Typography>
                              {experience.repoUrl && (
                                <Box sx={{ mt: 3, mb: 2 }}>
                                  <OgImage siteUrl={experience.repoUrl} />
                                </Box>
                              )}
                              {experience.repoUrl ? (
                                <Link
                                  sx={{ wordBreak: "break-all" }}
                                  target="_blank"
                                  href={experience.repoUrl}
                                >
                                  {experience.repoUrl}
                                </Link>
                              ) : (
                                ""
                              )}
                              {experience.problemSolvedDescription.length >
                                0 && (
                                <div>
                                  <Typography
                                    variant="subtitle1"
                                    sx={{ fontWeight: "bold", mt: 4 }}
                                  >
                                    Description
                                  </Typography>
                                  <Typography>
                                    {experience.problemSolvedDescription}
                                  </Typography>
                                </div>
                              )}
                              {experience.project_has_skills && (
                                <div>
                                  <Typography
                                    variant="subtitle1"
                                    sx={{ fontWeight: "bold", mt: 2 }}
                                  >
                                    Skills Demonstrated
                                  </Typography>
                                  <Skills
                                    skillsList={experience.project_has_skills.map(
                                      (item: JobseekerSkillDTO) => item.skills,
                                    )}
                                    maxNumSkills={0}
                                    color="default"
                                    key={experience.projectId + "skills"}
                                  />
                                </div>
                              )}
                            </Stack>
                          </Box>
                        </Box>
                      ))}
                    </Stack>
                  </Card>
                )}
              {/* Work Experience */}
              {jobseeker?.work_experiences &&
                jobseeker?.work_experiences.length > 0 && (
                  <Card sx={{ p: 2 }}>
                    <Stack
                      direction={"row"}
                      sx={{ justifyContent: "space-between" }}
                    >
                      <Typography variant="h5">Experience</Typography>
                      {isOwnProfile && (
                        <IconButton href="/edit-profile/jobseeker/work-experience">
                          <EditIcon />
                        </IconButton>
                      )}
                    </Stack>
                    <Stack
                      spacing={4}
                      sx={{ pl: 2 }}
                      divider={<Divider sx={{ my: 2 }} />}
                    >
                      {jobseeker.work_experiences.map((experience) => (
                        <Box key={experience.workId}>
                          <Stack>
                            <Typography variant="h6">
                              {experience.jobTitle} - {experience.company}
                            </Typography>
                            <Typography variant="subtitle2">
                              {
                                monthNames[
                                  new Date(experience.startDate).getMonth()
                                ]
                              }{" "}
                              {new Date(experience.startDate).getFullYear()} -{" "}
                              {experience.endDate
                                ? monthNames[
                                    new Date(experience.endDate).getMonth()
                                  ] +
                                  " " +
                                  new Date(experience.endDate).getFullYear()
                                : "Present"}
                            </Typography>
                          </Stack>
                          <Typography>{experience.responsibilities}</Typography>
                        </Box>
                      ))}
                    </Stack>
                  </Card>
                )}
            </Stack>
          </Grid>
        </Box>
      </Stack>
    </Container>
  );
}
