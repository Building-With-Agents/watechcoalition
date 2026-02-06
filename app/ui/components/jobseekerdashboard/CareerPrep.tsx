import { Card, Grid, Stack } from "@mui/material";
import Image from "next/image";
import { ReactNode } from "react";
import RoundedButton from "../RoundedButton";

export default async function CareerPrep() {
  //const Meetings = await getMeetingByJobSeeker(props.jobseekerId);

  const copy: {
    headline: string;
    body: ReactNode;
    button: string;
    buttonLink: string;
  } = {
    headline: "Access On-demand Career Preparation Skill Building Modules",
    body: "You've officially joined the program! You can now access the Canvas training and begin your journey.",
    button: "Access Canvas Training",
    buttonLink: "https://computingforall.instructure.com/enroll/JKT9EF",
  };
  //hotfix removed so people dont sign up
  // switch (props.enrollmentStatus) {
  //   case undefined:
  //     copy = {
  //       headline: "Your Journey Starts Here",
  //       body: (
  //         <div>
  //           Once you complete the skills assessment, you’ll be on your way to:
  //           <ul className="space-y-3 py-3">
  //             <li>A personalized Professional Development Plan</li>
  //             <li>A virtual meeting with our Career Navigator</li>
  //           </ul>
  //         </div>
  //       ),
  //       button: "Start",
  //       buttonLink: "/services/jobseekers/career-prep/skill-assessment",
  //     };
  //     break;
  //   case CareerPrepStatus.Applied:
  //   case CareerPrepStatus.CreatingPlan:
  //     copy = {
  //       headline: "Thank You for Taking the Skills Assessment",
  //       body: `We’re currently crafting a personalized Professional Development Plan just for you. Within 3-5 business days, you'll receive an email to schedule your first meeting with a dedicated Career Navigator.`,
  //       button: "Learn More",
  //       buttonLink: "/about-us", // TODO: onces there's an info page for carreer prep replace this
  //     };
  //     break;

  //   case CareerPrepStatus.PlanCreated:
  //     copy = {
  //       headline: "Your Personalized Plan is Ready!",
  //       body: "Your Professional Development Plan is ready for your review. Click below to schedule a meeting with our Career Navigator:",
  //       button: "Schedule a Meeting",
  //       buttonLink:
  //         "https://outlook.office365.com/owa/calendar/CFACareerServices@computingforall.org/bookings/", // Replace with the actual Bookings page link
  //     };
  //     break;

  //   case CareerPrepStatus.MeetingScheduled:
  //     copy = {
  //       headline: "Your Next Steps",
  //       body: (
  //         <div>
  //           You have an upcoming meeting(s) with {props.caseManager} scheduled
  //           for:
  //           <ul className="py-3">
  //             {Meetings.map((m) => (
  //               <li
  //                 className="text-lg font-bold text-black"
  //                 key={m.id}
  //               >{`${m.meetingDate}`}</li>
  //             ))}
  //           </ul>
  //         </div>
  //       ), // Replace placeholders with actual data
  //       button: "Reschedule Meeting",
  //       buttonLink:
  //         "https://outlook.office365.com/owa/calendar/CFACareerServices@computingforall.org/bookings/", // Replace with the actual Reschedule page link
  //     };
  //     break;

  //   case CareerPrepStatus.MetCareerNavigator:
  //     copy = {
  //       headline: "Complete Your Enrollment",
  //       body: `To officially join the program and access your Canvas training, please complete the enrollment form.`,
  //       button: "Enroll Now",
  //       buttonLink: "/services/jobseekers/career-prep/enrollment",
  //     };
  //     break;
  //   case CareerPrepStatus.Completed:
  //   case CareerPrepStatus.Enrolled:
  //     copy = {
  //       headline: "Welcome to Career Prep!",
  //       body: "You've officially joined the program! You can now access the Canvas training and begin your journey.",
  //       button: "Access Canvas Training",
  //       buttonLink: "https://computingforall.instructure.com/enroll/JKT9EF",
  //     };
  //     break;

  //   //TODO ask for copy for these Statuses
  //   case CareerPrepStatus.Rejected:
  //     copy = {
  //       headline: "Application Rejected",
  //       body: "Unfortunately, your application was not approved.",
  //       button: "Contact Us",
  //       buttonLink: "/services/jobseekers/career-prep/skill-assessment",
  //     };
  //     break;

  //   case CareerPrepStatus.Withdrawn:
  //     copy = {
  //       headline: "Application Withdrawn",
  //       body: "You have withdrawn from the program.",
  //       button: "Reapply",
  //       buttonLink: "/services/jobseekers/career-prep/skill-assessment",
  //     };
  //     break;

  //   default:
  //     copy = {
  //       headline: "Status Unknown",
  //       body: "We are unable to determine your status.",
  //       button: "Contact Support",
  //       buttonLink:
  //         "https://github.com/Computing-For-All/nextjs-issue-tracker/issues/new?assignees=&labels=uat&projects=Computing-For-All%2Fnextjs-issue-tracker&template=application.yml",
  //     };
  //     break;
  // }
  return (
    <Card
      elevation={0}
      sx={{
        borderRadius: "1rem",
        backgroundColor: "rgb(246 246 246 / var(--tw-bg-opacity, 1))",
        p: "1rem",
      }}
    >
      <Stack direction={{ sx: "column", lg: "row" }} gap={2}>
        <Image
          className="rounded-2xl"
          width={400}
          height={267}
          src="/images/stock/careerAssesment.jfif"
          alt="4 people looking at a computer, ready to start their journey"
        />
        <Grid container gap={2} direction={"column"}>
          <div>
            <p className="self-stretch text-[32px] font-normal leading-[38.40px] text-secondary-main">
              {copy.headline}
            </p>
            {/* <div className="inline-flex h-4 items-start justify-start gap-2.5 self-stretch">
              <p className="font-semibold leading-none tracking-wider text-primary-main">
                Career Prep Program
              </p>
            </div> */}
            {/* <div className="font-normal leading-tight text-neutral-900/60">
              {copy.body}
            </div> */}
          </div>
          <RoundedButton
            snug
            invertColor
            link={copy.buttonLink}
            content={copy.button}
          />
        </Grid>
      </Stack>
    </Card>
  );
}
