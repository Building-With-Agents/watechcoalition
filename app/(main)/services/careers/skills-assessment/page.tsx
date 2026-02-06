import CareerPill from "@/app/ui/components/career/CareerPill";

export default function Page() {
  return (
    <div className="bg-white flex-col justify-start items-center">
      <div className="mx-auto p-[48px] max-w-[80vw]">
        {/* p-8 px-8 md:px-12 lg:px-16 */}
        <div className="self-stretch flex-col justify-center items-start flex">
          <div className="self-stretch mb-4 text-sky-900 text-4xl tablet:text-6xl font-normal font-['Roboto'] leading-tight">
            {/* Careers In IT & Cybersecurity */}
          </div>
          <div className="self-stretch text-zinc-900 text-xl font-normal font-['Roboto'] leading-loose pb-8">
            <div className="container mx-auto flex flex-col items-center px-8 md:px-12 lg:px-16">
              <div className="text-center">
                Skills Asssessment
                <br />
                <span className="font-['Roboto'] text-6xl font-normal leading-[84px] text-secondary-main">
                  Your Tech Career—
                  <br />
                </span>
                <span className="font-['Roboto'] text-6xl font-medium leading-[84px] text-secondary-main">
                  Personalized.
                </span>
              </div>
              <div className="text-[32px] text-center py-3">
                Discover your strengths and gain personalized job
                recommendations.
              </div>
            </div>

            <p>
              Finding the right tech job can be overwhelming. Our skills
              assessment simplifies the process. By understanding your
              strengths, we connect you with Career Services Navigators who
              personalize your job search, matching you with roles where you can
              excel. Take the assessment today and get one step closer to your
              dream tech career. <strong>(400 characters max)</strong>
            </p>

            <div className="laptop:hidden block text-[28px] text-center text-error-main pt-8">
              <p>
                For the best experience, please take the skills assessment on a
                desktop or laptop computer.
              </p>
            </div>
          </div>
        </div>
        <div className="hidden laptop:grid grid-cols-1 tablet:grid-cols-2 pt-8 sm-tablet:p-12 justify-center items-center gap-12">
          <CareerPill
            title={"Software Developer"}
            // subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/software-developer.jpg"}
            href={"/services/careers/software-developer"}
          />

          <CareerPill
            title={"IT/Cloud Support"}
            // subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/it-cloud-support.jpg"}
            href={"/services/careers/it-cloud-support"}
          />

          <CareerPill
            title={"Cybersecurity"}
            // subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/cybersecurity.jpg"}
            href={"/services/careers/cybersecurity"}
          />

          <CareerPill
            title={"Data Analytics"}
            // subtitle={"$100k avg. salary | 1 - 2 year programs"}
            img={"/images/careers/data-analytics.jpg"}
            href={"/services/careers/data-analytics"}
          />
        </div>
      </div>
    </div>
  );
}
