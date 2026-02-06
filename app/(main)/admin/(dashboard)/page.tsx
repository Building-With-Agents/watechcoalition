import {
  getGenderBreakDownOfJobseekers,
  getUsersCreatedByQuarter,
} from "@/app/lib/admin/stats";
import { PieChart } from "@mui/x-charts/PieChart";
import { BarChart } from "@mui/x-charts/BarChart";
//employer dashboard
export const metadata = {
  title: "My Dashboard",
};
export default async function Page() {
  return (
    <main className="space-y-3 py-8 font-['Roboto'] bg-gray-bg grow px-[50px]">
      <h1 className="text-2xl font-medium">Stats:</h1>
      <GenderPie />
      <NewUsersByQuarter />
    </main>
  );
}

async function GenderPie() {
  const genderBreakdownOfJobSeekers = await getGenderBreakDownOfJobseekers();
  const chartData = Object.entries(genderBreakdownOfJobSeekers).map(
    ([gender, value], index) => ({
      id: index,
      value,
      label: (gender.length > 0 ? gender : "UNKNOWN") + `: ${value}`,
    }),
  );
  return (
    <div className="text-center w-fit">
      <h3 className="text-xl">Gender Breakdown Of Jobseekers</h3>
      <PieChart
        series={[
          {
            data: chartData,
          },
        ]}
        width={600}
        height={200}
      />
    </div>
  );
}

async function NewUsersByQuarter() {
  const data = await getUsersCreatedByQuarter();
  const xAxis = data.map((item) => `${item.year}-Q${item.quarter}`);
  const seriesData = data.map((item) => item.userCount);
  return (
    <div className="text-center w-fit">
      <h3 className="text-xl">Number Of New Users By Quarter</h3>
      <BarChart
        xAxis={[{ scaleType: "band", data: xAxis }]}
        series={[{ data: seriesData }]}
        width={600}
        height={300}
      />
    </div>
  );
}
