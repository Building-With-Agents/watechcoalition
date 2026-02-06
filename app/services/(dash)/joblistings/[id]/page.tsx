import { getJobListingById } from "@/app/lib/joblistings";
import JobPostingPage from "@/app/ui/components/jobPostings/JobPostingPage";
import Link from "next/link";
import { auth } from "@/auth";

export default async function page(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const session = await auth();
  const joblisting: any = await getJobListingById(
    params.id,
    session?.user.jobseekerId ?? undefined,
  );

  if (joblisting == null || joblisting == undefined) {
    return (
      <main className="h-screen text-center space-y-3 py-8 ml-4 tablet:mx-[150px] laptop:mx-[200px]">
        <h1 className="text-4xl">Job Listing Not Found</h1>
        <Link href="/services/joblistings" className="LINK">
          Find Active Job Listings Here
        </Link>
      </main>
    );
  }
  if (joblisting.jobApplications && joblisting.jobApplications[0]) {
    const connectedJobApplication = joblisting.jobApplications[0];
    const listingWithJobseeker = {
      ...joblisting,
      jobStatus: connectedJobApplication.jobStatus ?? "",
      isBookmarked: connectedJobApplication?.isBookmarked ?? false,
      job_posting_id: joblisting?.job_posting_id ?? "",
    };
    return <JobPostingPage joblisting={listingWithJobseeker} params={params} />;
  } else {
    return <JobPostingPage joblisting={joblisting} params={params} />;
  }
}
