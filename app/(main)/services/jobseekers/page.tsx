import CircleBlurb from "@/app/ui/components/CircleBlurb";
import TimeLine from "@/app/ui/components/TimeLine";
import BottomFoldJobSeeker from "@/app/ui/components/BottomFoldJobseeker";
import JobSeekerPageBanner from "@/app/ui/components/JobSeekerPageBanner";

/**
 * @returns Job seeker landing page
 */
export default function Page() {
  return (
    <div className="font-roboto">
      <JobSeekerPageBanner />
      <div className="container mx-auto flex flex-col items-center space-y-8 px-8 py-16 md:px-12 lg:px-16">
        <div className="text-center">
          <span className="font-['Roboto'] text-6xl font-normal leading-[66px] text-secondary-main">
            It&apos;s Not a Job Board—
            <br />
            It&apos;s a{" "}
          </span>
          <span className="font-['Roboto'] text-6xl font-medium leading-[66px] text-primary-main">
            Launchpad
          </span>
        </div>
        <div className="text-center font-['Roboto'] text-2xl font-normal leading-relaxed text-[#0f1728]">
          Our Talent Portal is designed to help you position yourself as a top
          job candidate in today&apos;s digital world
        </div>
        <br />
        <CircleBlurb />
        <div className="text-center">
          <span className="text-secondary-main text-6xl font-normal font-['Roboto'] capitalize leading-[66px]">
            Talent{" "}
          </span>
          <span className="text-primary-main text-6xl font-normal font-['Roboto'] capitalize leading-[66px]">
            Portal
          </span>
        </div>
        <div className="text-center text-[#0f1728] text-2xl font-normal font-['Roboto'] leading-relaxed">
          Our Talent Portal is designed to help you position yourself as a top
          job candidate in today&apos;s digital world
        </div>
        <br />
        <TimeLine />
      </div>
      <BottomFoldJobSeeker />
    </div>
  );
}
