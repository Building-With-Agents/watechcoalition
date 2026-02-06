import { getAllJobSeekerCardView } from "@/app/lib/prisma";
import JobSeekerCardView from "@/app/ui/components/JobSeekerCardView";

export default async function FeaturedCandidates({
  maxCandidates,
}: {
  maxCandidates: number | null;
}) {
  let jobSeekers = await getAllJobSeekerCardView();

  try {
    // Attempt to fetch job seekers data
    jobSeekers = await getAllJobSeekerCardView();

    // Ensure jobSeekers is an array before performing operations
    if (
      Array.isArray(jobSeekers) &&
      maxCandidates != null &&
      jobSeekers.length > maxCandidates
    ) {
      // Safely slice the array if needed
      jobSeekers = jobSeekers.slice(0, maxCandidates);
      // TODO: actually feature candidates. filter based on industry? randomize results? sort by yearsExp?
      // at least limit results so we don't return/parse every jobseeker...
    }
  } catch (error) {
    console.error("Failed to fetch or process job seekers:", error);
    // Log the error and fail gracefully without breaking the page
    jobSeekers = []; // Set jobSeekers to an empty array to continue rendering
  }

  return (
    <div>
      <h2 className="text-lg font-bold py-5">Featured Candidates</h2>
      <div className="grid laptop:grid-cols-3 gap-2">
        {jobSeekers?.map((jobSeeker: any) => (
          <JobSeekerCardView
            jobseeker={jobSeeker}
            isBookmarked={false}
            key={jobSeeker.jobseeker_id}
          />
        ))}
      </div>
    </div>
  );
}
