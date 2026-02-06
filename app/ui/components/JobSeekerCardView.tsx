"use client";
import Avatar from "./Avatar";
import Skills from "./Skills";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { JobseekerSkillDTO } from "@/data/dtos/JobseekerSkillDTO";
import { JobSeekerCardViewDTO } from "@/data/dtos/JobSeekerCardViewDTO";
import ShareButton from "./ShareButton";
import Link from "next/link";
import { useSession } from "next-auth/react";
import { ProgramEnrollmentStatus } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { Role } from "@/data/dtos/UserInfoDTO";
import Bookmark from "./Bookmark";
import { ShareIcon } from "@heroicons/react/24/outline";

export default function JobSeekerCardView({
  jobseeker,
  isBookmarked = false,
}: {
  jobseeker: JobSeekerCardViewDTO;
  isBookmarked: boolean;
}) {
  const { data: session } = useSession();

  const name: string =
    jobseeker?.users?.first_name + " " + jobseeker?.users?.last_name;
  // const pathway: string = jobseeker?.pathways?.pathway_title ?? '';
  const pfpPicSrc: string = jobseeker?.users?.photo_url ?? "";
  const aboutMe: string = jobseeker?.intro_headline ?? "";
  const id: string = jobseeker?.jobseeker_id;
  const industry: string =
    [
      ...new Set(
        jobseeker?.work_experiences?.map(
          (ind) => ind.industrySector?.sector_title,
        ),
      ),
    ]
      .toString()
      .replaceAll(",", ", ") ?? "";
  const location: string =
    jobseeker?.users?.locationData?.city +
    ", " +
    jobseeker?.users?.locationData?.state +
    " " +
    jobseeker?.users?.locationData?.zip;
  const skills: SkillDTO[] = jobseeker?.jobseeker_has_skills
    ? jobseeker?.jobseeker_has_skills.map(
        (item: JobseekerSkillDTO) => item.skills,
      )
    : [];

  // Decide what school to show
  let school = "";
  if (
    jobseeker?.jobseeker_education &&
    jobseeker.jobseeker_education.length > 0
  ) {
    // Check if the jobseeker is currently enrolled in any education program
    const enrolledEducation = jobseeker.jobseeker_education.find(
      (edu) => edu.enrollmentStatus == ProgramEnrollmentStatus.Enrolled,
    );

    if (enrolledEducation) {
      // If there is an enrolled program, prioritize that
      school =
        (enrolledEducation.eduProviders?.name || "") +
        " | " +
        (enrolledEducation?.degreeType || "") +
        (enrolledEducation.program?.title
          ? " | " + enrolledEducation?.program?.title
          : "");
    } else {
      // If no enrolled program is found, show the first available education
      const firstEducation = jobseeker.jobseeker_education[0];
      school =
        (firstEducation.eduProviders?.name || "") +
        " | " +
        (firstEducation?.degreeType || "") +
        (firstEducation?.program?.title
          ? " | " + firstEducation.program.title
          : "");
    }
  }

  const showBookmarks =
    session?.user.roles.includes(Role.EMPLOYER) && // check role for permissions
    session.user.companyId != undefined && // company is set
    session?.user.employeeIsApproved; // employee must be approved to edit this company

  return (
    <div className="w-full rounded-lg border border-2 border-cyan-600 p-2 phone:p-4">
      {/* top row */}
      <div className="flex flex-row items-center">
        {/* picture */}
        <div className="shrink-0">
          <Avatar imgsrc={pfpPicSrc} />
        </div>

        {/* name and info */}
        <div className="grow pl-2 sm-tablet:pl-4">
          <p className="text-wrap font-bold">{name}</p>
          <p className="text-wrap text-sm sm-tablet:text-base">{industry}</p>
          {/* <p className="text-wrap text-slate-400 text-sm">{yearsExp}, highest degree: {highestDegree}</p> */}
          <p className="text-wrap text-sm text-slate-400 sm-tablet:text-base">
            {location}
          </p>
        </div>

        {/* view and share */}
        <div className="flex flex-col">
          {/* {showViewProfile ? // only show View Profile if it's your Jobseeker profile */}
          <div className="h-min w-max">
            <Link // view profile should redirect to login and then continue to candidate after account create
              href={"/services/jobseekers/" + id}
              className="inline-block w-fit rounded-full border border-2 border-cyan-600 bg-white px-2 py-2 text-sm text-cyan-600 hover:bg-gray-200 tablet:px-4 tablet:text-base laptop:px-6 laptop:text-lg"
            >
              <strong>View Profile</strong>
            </Link>
          </div>
          {/* : ""} */}
          <div className="mr-2 mt-2 flex flex-row place-self-end text-cyan-600">
            {showBookmarks ? (
              <Bookmark
                bookmarked={isBookmarked}
                addUrl={
                  "/api/companies/bookmark/addJobseeker/" +
                  jobseeker.jobseeker_id
                }
                removeUrl={
                  "/api/companies/bookmark/removeJobseeker/" +
                  jobseeker.jobseeker_id
                }
              />
            ) : (
              ""
            )}
            <ShareButton href={"/services/jobseekers/" + id}>
              <ShareIcon className="h-10 w-10 stroke-2" />
            </ShareButton>
          </div>
        </div>
      </div>

      {/* bottom row */}
      <div className="mt-2">
        {/* about me */}
        <p className="line-clamp-3">{aboutMe}</p>

        {/* school */}
        <h4 className="mt-2 text-sm italic text-slate-400">{school}</h4>

        {/* skills */}
        <div className="mt-2 flex grow text-sm tablet:text-base">
          <Skills skillsList={skills} maxNumSkills={5} jobseekerID={id} />
        </div>
      </div>
    </div>
  );
}
