export const dynamic = "force-dynamic";
import { getAllPreScreenedCareerPrepStudents } from "@/app/lib/admin/careerPrep";
import CareerPrepDataGrid from "@/app/ui/components/careerPrep/CareerPrepDataGrid";
export const metadata = {
  title: "My Dashboard",
};
export default async function Page() {
  const clients = await getAllPreScreenedCareerPrepStudents();
  return (
    <main className="space-y-3 py-8 font-['Roboto'] bg-gray-bg grow px-[50px]">
      <h1 className="text-2xl font-medium">Showcase Eligible Candidates</h1>
      <CareerPrepDataGrid clients={clients} ShowClaimButton={false} />
    </main>
  );
}
