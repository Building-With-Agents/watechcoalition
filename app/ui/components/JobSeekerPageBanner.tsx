import RoundedButton from "./RoundedButton";
import { auth } from "@/auth";

export default async function JobSeekerPageBanner() {
  const session = await auth();
  console.log("session is ", session);
  //h-[615px] content-center bg-jobseeker-hero-1 bg-cover bg-center p-4 text-white bg-blend-darken tablet:p-10 laptop:h-[854px] laptop:p-20 bg-linear-to-r from-purple-500 to-blue-tw500
  return (
    <div
      className={
        "h-[750px] px-[16px] sm-tablet:px-[50px] laptop:h-[854px] laptop:px-[100px] content-center bg-jobseeker-hero-1 bg-cover bg-center"
      }
    >
      <div className="inline-flex  max-w-[557px] flex-col items-start justify-start gap-4">
        <div className="self-stretch font-['Roboto'] text-6xl font-normal capitalize leading-[66px] text-white">
          Showcase your skills and get discovered by employers
        </div>
        <div className="max-w-[540.10px] font-['Roboto'] text-2xl font-normal leading-relaxed text-white">
          Stand Out and Unlock New Opportunities
        </div>
        <div className="flex flex-col items-start justify-start">
          <div className="relative h-6 w-px" />
        </div>
        {session == null ? (
          <RoundedButton
            content={"Create Profile"}
            link={"/signin"}
            invertColor={false}
          />
        ) : (
          ""
        )}
      </div>
    </div>
  );
}
