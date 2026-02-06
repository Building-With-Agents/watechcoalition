import { EduProviderPathways } from "@/app/lib/eduProviders";
import CareerPage from "@/app/ui/components/career/CareerPage";

export default function Page() {
  return (
    <>
      <CareerPage
        title={"IT/Cloud Support"}
        subtitle={"Keep systems running smoothly and securely"}
        img={"/images/careers/it-cloud-support.jpg"}
        altCareerNames={
          "IT Support Specialist, Technical Support Engineer, Cloud Support Engineer, Systems Administrator, Service Desk Analyst, Network Support Specialist, Desktop Support Technician, Customer Support Engineer, IT Operations Analyst, Cloud Infrastructure Engineer, DevOps Support Engineer, Cloud Solutions Specialist, Platform Support Specialist"
        }
        avgSalary={"$100K/year"}
        trainingLength={"1 - 2 Years"}
        prepLevel={"Medium"}
        description={
          "IT/Cloud Support Specialists maintain IT infrastructure, resolve technical issues, and manage cloud solutions. They ensure that systems run smoothly and securely, enabling teams to work efficiently across an organization."
        }
        whatYoullDo={
          "Troubleshoot and maintain IT infrastructure, support cloud solutions, and resolve technical issues for users"
        }
        skillsYoullNeed={
          "Knowledge of cloud platforms, troubleshooting skills, and a problem-solving mindset"
        }
        whyItMatters={
          "You’ll ensure seamless operations, empowering teams to work efficiently and securely"
        }
        trainingPrograms={EduProviderPathways.ITCloudSupport}
      />
      {/* Commented out Lightcast data link. It's not ready for public view */}
      {/*<div className="bg-neutral-100 flex-col justify-start items-center inline-flex">*/}
      {/*    <div className="self-stretch px-32 bg-white flex-col justify-start items-center gap-2.5 flex">*/}
      {/*    <div className="self-stretch px-24 flex-col justify-center items-start gap-2.5 flex">*/}
      {/*        <div className="text-sky-900 text-3xl font-medium font-['Roboto'] leading-10">Lightcast Data</div>*/}
      {/*        <div className="self-stretch text-zinc-900 text-base font-normal font-['Roboto'] leading-tight">*/}
      {/*        <Link href={"https://www.watechwfcoalition.org/ess/occupation/8b71acdf-cf5f-ef11-bfe3-6045bd00eb93"}>*/}
      {/*            <div className="px-5 py-3 bg-neutral-100 rounded-full justify-center items-center gap-1.5 flex">*/}
      {/*                <button className="text-center text-sky-900 text-base font-medium font-['Roboto'] capitalize leading-tight tracking-tight">See More</button>*/}
      {/*            </div>*/}
      {/*        </Link>*/}
      {/*        </div>*/}
      {/*    </div>*/}
      {/*    </div>*/}
      {/*</div>*/}
      <div className="flex-col justify-start items-start flex">
        <div className="w-px h-20 relative" />
      </div>
    </>
  );
}
