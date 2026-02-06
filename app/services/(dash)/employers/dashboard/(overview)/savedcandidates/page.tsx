import { getJobseekerBookmarkByCompany } from "@/app/lib/prisma";
import JobSeekerCardView from "@/app/ui/components/JobSeekerCardView";
import Link from "next/link";

export default async function Page() {
  const bookmarkedJobseekers = await getJobseekerBookmarkByCompany();

  return (
    <main className="m-2 mb-0 w-full space-y-4 pt-8 phone:m-4 phone:p-6 sm-tablet:m-6 laptop:px-[200px]">
      <h1 className="text-2xl font-medium">Saved Candidates</h1>
      <div className="space-y-4">
        {bookmarkedJobseekers == null || bookmarkedJobseekers.length < 1 ? (
          <div>
            <p>
              No Saved Candidates Found:{" "}
              <Link
                href={"/services/employers/dashboard/talent-search"}
                className="LINK"
              >
                Find Candidates here
              </Link>
            </p>
          </div>
        ) : (
          bookmarkedJobseekers?.map((jobseeker) => {
            return (
              <JobSeekerCardView
                jobseeker={{
                  jobseeker_id: jobseeker.jobseekerId,
                  user_id: jobseeker.jobseeker.user_id,
                  BookmarkedJobseeker: jobseeker.jobseeker.BookmarkedJobseeker,
                  intro_headline: jobseeker.jobseeker.intro_headline,
                  years_work_exp: jobseeker.jobseeker.years_work_exp,
                  highest_level_of_study_completed:
                    jobseeker.jobseeker.highest_level_of_study_completed,
                  pathways: jobseeker.jobseeker.pathways,
                  work_experiences: jobseeker.jobseeker.work_experiences,
                  users: jobseeker.jobseeker.users,
                  jobseeker_education: jobseeker.jobseeker.jobseeker_education, //TODO needs fixing to match dtos
                  jobseeker_has_skills:
                    jobseeker.jobseeker.jobseeker_has_skills,
                }}
                isBookmarked={true}
                key={jobseeker.jobseekerId}
              />
            );
          })
        )}
      </div>
    </main>
  );
}
