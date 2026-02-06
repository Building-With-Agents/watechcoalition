import { getUnManagedCareerPrepStudents } from "@/app/lib/admin/careerPrep";
import CareerPrepDataGrid from "@/app/ui/components/careerPrep/CareerPrepDataGrid";
export const metadata = {
  title: "My Dashboard",
};
export default async function Page() {
  const clients = await getUnManagedCareerPrepStudents();
  return (
    <main className="space-y-3s">
      <h1 className="text-2xl font-medium">New Students</h1>
      <div className="max-w-10/12">
        <CareerPrepDataGrid clients={clients} ShowClaimButton={true} />
      </div>
    </main>
  );
}
