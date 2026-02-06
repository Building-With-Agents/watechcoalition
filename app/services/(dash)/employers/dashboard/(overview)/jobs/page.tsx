import { getCompanyById, getEmployerById } from "@/app/lib/prisma";
import JobsManagementPageContent from "@/app/ui/components/jobManagement/JobsManagementPageContent";
import { auth } from "@/auth";

export const metadata = {
  title: "Job Management",
};

export default async function Page() {
  const session = await auth();

  const proInfo = await getEmployerById(session?.user.employerId ?? "");
  const company = await getCompanyById(proInfo?.company_id ?? "");

  if (!proInfo || company == undefined) {
    return (
      <div>
        <h1 className="text-2xl">
          There has been an error finding your info please try logging out and
          logging back in
        </h1>
      </div>
    );
  }
  return <JobsManagementPageContent />;
}
