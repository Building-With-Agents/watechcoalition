import { companies } from "@/app/lib/data";
import BottomFold from "@/app/ui/components/employerLanding/BottomFold";
import EmployerPageBanner from "@/app/ui/components/employerLanding/EmployerPageBanner";

export default function Page() {
  return (
    <>
      <EmployerPageBanner />
      <main className="space-y-12 font-['Roboto'] ">
        <div className="space-y-12 mx-2 tablet:px-4 laptop:mx-8">
          <div className="text-center mt-20">
            <h2 className="self-stretch text-cyan-700 text-5xl font-normal font-['Roboto'] capitalize leading-10">
              Companies Hiring Through the Coalition
            </h2>
          </div>
          <div className="grid grid-cols-1 tablet:grid-cols-2 laptop:grid-cols-3 desktop:grid-cols-4 gap-4 mt-4">
            {companies.map((company, index) => (
              <div
                key={index}
                className="justify-center items-center h-22 px-7 py-4 bg-neutral-100 rounded-3xl flex-col gap-2.5 inline-flex"
              >
                <p className="text-base text-center font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                  {company}
                </p>
              </div>
            ))}
          </div>
        </div>
        <BottomFold />
      </main>
    </>
  );
}
