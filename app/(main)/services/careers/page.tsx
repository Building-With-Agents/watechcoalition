import CareerPill from "@/app/ui/components/career/CareerPill";
import Image from "next/image";

export default function Page() {
  return (
    <div className="bg-white flex-col justify-start items-center">
      <div className="bg-sky-900">
        <Image
          src="/images/careers/careers.jpg"
          width={4096}
          height={2731}
          alt="Stock photo"
          className="w-full"
        />
        <div className="hidden p-12 tablet:inline-flex tablet:left-[48px] tablet:top-[500px] tablet:absolute bg-sky-950/90 rounded-3xl flex-col justify-end items-center gap-2.5 inline-flex">
          <div className="self-stretch text-neutral-100 text-6xl font-normal font-['Roboto'] leading-10">
            Start Your Journey In Tech
          </div>
          <div className="self-stretch text-sky-200 text-xl font-normal font-['Roboto'] capitalize leading-loose">
            explore in-demand tech careers that align with your passions and
            expertise
          </div>
        </div>
      </div>

      <div className="p-8 px-12">
        <div className="self-stretch flex-col justify-center items-start flex">
          <div className="self-stretch mb-4 text-sky-900 text-4xl tablet:text-6xl font-normal font-['Roboto'] leading-tight">
            Careers In IT & Cybersecurity
          </div>
          <div className="self-stretch text-zinc-900 text-xl font-normal font-['Roboto'] leading-loose">
            {
              "Explore impactful careers that shape the future of technology. Whether you're a developer at heart or a data guru, we have a place for you. Dive into the roles, find your fit, and embark on a career journey that resonates with your skills and aspirations. Each career path offers unique opportunities to innovate, solve problems, and lead in the digital age."
            }
          </div>
        </div>

        <div className="grid grid-cols-1 tablet:grid-cols-2 pt-8 sm-tablet:p-12 justify-center items-center gap-12">
          <CareerPill
            title={"Software Developer"}
            subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/software-developer.jpg"}
            href={"/services/careers/software-developer"}
          />

          <CareerPill
            title={"IT/Cloud Support"}
            subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/it-cloud-support.jpg"}
            href={"/services/careers/it-cloud-support"}
          />

          <CareerPill
            title={"Cybersecurity"}
            subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/cybersecurity.jpg"}
            href={"/services/careers/cybersecurity"}
          />

          <CareerPill
            title={"Data Analytics"}
            subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/data-analytics.jpg"}
            href={"/services/careers/data-analytics"}
          />
        </div>
      </div>
    </div>
  );
}
