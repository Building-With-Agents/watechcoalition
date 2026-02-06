import { Card, Grid, Stack } from "@mui/material";
import Carousel from "../Carousel";
import PillButton from "../PillButton";

export default async function AnnouncementSpace() {
  return (
    <Card
      elevation={0}
      sx={{
        backgroundColor: "neutral.100",
        p: "1rem",
      }}
    >
      <Grid direction="row" spacing={2}>
        <div className="justify-center text-primary-main text-base font-semibold uppercase leading-none mb-2">
          Talent Portal Guide
        </div>
        <div className="justify-center text-secondary-main text-3xl font-normal leading-10 mb-2">
          Welcome to the Talent Portal!
        </div>
        <div className="justify-center text-text-primary text-base font-normal leading-tight">
          This guide will help you navigate the platform and make the most of
          your journey to a technology career.
        </div>
      </Grid>
      <Carousel>
        {/* Career Prep Card with Enrollment & Info Buttons */}
        {/*<Card*/}
        {/*  elevation={0}*/}
        {/*  sx={{*/}
        {/*    borderRadius: "1rem",*/}
        {/*    p: "calc(var(--spacing) * 4)",*/}
        {/*    width: "100%",*/}
        {/*    height: "100%",*/}
        {/*  }}*/}
        {/*>*/}
        {/*  <Stack direction="column" gap={2}>*/}
        {/*    /!* Headline *!/*/}
        {/*    <p className="self-stretch text-[32px] font-normal leading-[38.40px] text-secondary-main">*/}
        {/*      Join the Career Prep Program*/}
        {/*    </p>*/}

        {/*    /!* Benefit-driven subheadline *!/*/}
        {/*    <div className="inline-flex items-start justify-start gap-2.5 self-stretch">*/}
        {/*      <p className="font-semibold leading-none tracking-wider text-primary-main">*/}
        {/*        Free workshops, personalized support, and access to a job*/}
        {/*        placement pool.*/}
        {/*      </p>*/}
        {/*    </div>*/}

        {/*    /!* Supporting motivation *!/*/}
        {/*    <div className="font-normal leading-tight text-neutral-900/60 w-[50vw]">*/}
        {/*      <p>*/}
        {/*        CFA Career Prep helps Washington tech grads build confidence,*/}
        {/*        expand their network, and launch their careers by joining the*/}
        {/*        next cohort.*/}
        {/*      </p>*/}
        {/*    </div>*/}

        {/*    /!* CTA Button *!/*/}
        {/*    <Stack*/}
        {/*      direction="row"*/}
        {/*      spacing={2}*/}
        {/*      sx={{ placeSelf: "end", mt: "calc(var(--spacing) * 4)" }}*/}
        {/*    >*/}
        {/*      <PillButton*/}
        {/*        color="secondary"*/}
        {/*        href="/services/jobseekers/career-prep/apply"*/}
        {/*      >*/}
        {/*        Apply*/}
        {/*      </PillButton>*/}
        {/*    </Stack>*/}
        {/*  </Stack>*/}
        {/*</Card>*/}

        {/* Update your profile card */}
        <Card
          elevation={0}
          sx={{
            borderRadius: "1rem",
            p: "calc(var(--spacing) * 4)",
            width: "100%",
            height: "100%",
          }}
        >
          <Stack direction={{ sx: "column" }} gap={2}>
            <p className="self-stretch text-[32px] font-normal leading-[38.40px] text-secondary-main">
              Keep Your Profile Up to Date
            </p>
            <div className="inline-flex items-start justify-start gap-2.5 self-stretch">
              <p className="font-semibold leading-none tracking-wider text-primary-main">
                Your Talent Portal profile is key to showcasing your skills and
                experience to potential employers.
              </p>
            </div>
            <div className="font-normal leading-tight text-neutral-900/60 w-[50vw]">
              <p>
                To maximize your opportunities and stand out to employers, we
                encourage you to complete and maintain your{" "}
                <strong>
                  introduction, skills, education history, work experience, and
                  resume.
                </strong>
              </p>
            </div>
            <PillButton
              color="secondary"
              href="/edit-profile/jobseeker/introduction"
              sx={{
                placeSelf: "end",
                mt: "calc(var(--spacing) * 4)",
              }}
            >
              Update Profile
            </PillButton>
          </Stack>
        </Card>
        {/* Find and apply for jobs card */}
        <Card
          elevation={0}
          sx={{
            borderRadius: "1rem",
            p: "calc(var(--spacing) * 4)",
            width: "100%",
            height: "100%",
          }}
        >
          <Stack direction={{ sx: "column" }} gap={2}>
            <p className="self-stretch text-[32px] font-normal leading-[38.40px] text-secondary-main">
              Find and Apply for Jobs
            </p>
            <div className="inline-flex items-start justify-start gap-2.5 self-stretch">
              <p className="font-semibold leading-none tracking-wider text-primary-main">
                We've built strong partnerships with employers to offer you
                targeted job opportunities.
              </p>
            </div>
            <div className="font-normal leading-tight text-neutral-900/60 w-[50vw]">
              <p>
                Our system analyzes your skills and experience to connect you
                with ideal roles, then our team reviews your qualifications and
                schedules a pre-screening meeting to prepare you for the
                application process. If you're a top candidate, we'll directly
                recommend you to the employer, boosting your chances of securing
                an interview and being considered for the role.
              </p>
            </div>
            <PillButton
              color="secondary"
              href="/services/joblistings"
              sx={{
                placeSelf: "end",
                mt: "calc(var(--spacing) * 4)",
              }}
            >
              Search for Jobs
            </PillButton>
          </Stack>
        </Card>
        {/* Attend events card */}
        {/*<Card*/}
        {/*  elevation={0}*/}
        {/*  sx={{*/}
        {/*    borderRadius: "1rem",*/}
        {/*    p: "calc(var(--spacing) * 4)",*/}
        {/*    width: "100%",*/}
        {/*    height: "100%",*/}
        {/*  }}*/}
        {/*>*/}
        {/*  <Stack direction={{ sx: "column" }} gap={2}>*/}
        {/*    <p className="self-stretch text-[32px] font-normal leading-[38.40px] text-secondary-main">*/}
        {/*      Attend Events*/}
        {/*    </p>*/}
        {/*    <div className="inline-flex items-start justify-start gap-2.5 self-stretch">*/}
        {/*      <p className="font-semibold leading-none tracking-wider text-primary-main">*/}
        {/*        Join our Events & Workshops!*/}
        {/*      </p>*/}
        {/*    </div>*/}
        {/*    <div className="font-normal leading-tight text-neutral-900/60 w-[50vw]">*/}
        {/*      <p>*/}
        {/*        We offer monthly sessions led by industry professionals,*/}
        {/*        covering essential skills and the latest industry knowledge. And*/}
        {/*        because we know life gets busy, all workshops are recorded and*/}
        {/*        available online.*/}
        {/*      </p>*/}
        {/*    </div>*/}
        {/*    <PillButton*/}
        {/*      color="secondary"*/}
        {/*      href="/services/events"*/}
        {/*      sx={{*/}
        {/*        placeSelf: "end",*/}
        {/*        mt: "calc(var(--spacing) * 4)",*/}
        {/*      }}*/}
        {/*    >*/}
        {/*      View Events*/}
        {/*    </PillButton>*/}
        {/*  </Stack>*/}
        {/*</Card>*/}
        {/* Join the community card */}
        {/*<Card*/}
        {/*  elevation={0}*/}
        {/*  sx={{*/}
        {/*    borderRadius: "1rem",*/}
        {/*    p: "calc(var(--spacing) * 4)",*/}
        {/*    width: "100%",*/}
        {/*    height: "100%",*/}
        {/*  }}*/}
        {/*>*/}
        {/*  <Stack direction={{ sx: "column" }} gap={2}>*/}
        {/*    <p className="self-stretch text-[32px] font-normal leading-[38.40px] text-secondary-main">*/}
        {/*      Join the Community*/}
        {/*    </p>*/}
        {/*    <div className="inline-flex items-start justify-start gap-2.5 self-stretch">*/}
        {/*      <p className="font-semibold leading-none tracking-wider text-primary-main"></p>*/}
        {/*    </div>*/}
        {/*    <div className="font-normal leading-tight text-neutral-900/60 w-[50vw]">*/}
        {/*      <p>*/}
        {/*        Our tech community provides you with access to a supportive*/}
        {/*        environment where you can explore our comprehensive resource*/}
        {/*        library, learn from industry experts, find groups based on your*/}
        {/*        career goals and interests, join discussions, and build your*/}
        {/*        network.*/}
        {/*      </p>*/}
        {/*    </div>*/}
        {/*    <PillButton*/}
        {/*      color="secondary"*/}
        {/*      href="https://forum.watechwfcoalition.org/"*/}
        {/*      sx={{*/}
        {/*        placeSelf: "end",*/}
        {/*        mt: "calc(var(--spacing) * 4)",*/}
        {/*      }}*/}
        {/*    >*/}
        {/*      Join the Community*/}
        {/*    </PillButton>*/}
        {/*  </Stack>*/}
        {/*</Card>*/}
        {/* TODO: Explore career services card, once that feature is complete */}
      </Carousel>
    </Card>
  );
}
