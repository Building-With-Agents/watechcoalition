import { auth } from "@/auth";
import RoundedButton from "./RoundedButton";

export default async function BottomFoldJobSeeker() {
  const session = await auth();
  return (
    <div className="bg-jobseeker-bottom-1 bg-cover bg-right desktop:bg-top inline-flex h-[579px] w-full flex-col justify-center bg-linear-to-bl from-[#01171c] to-[#01171c] phone:p-[16px] tablet:p-[100px]">
      <div className="flex h-[294px] flex-col items-start justify-start gap-4">
        <div className="self-stretch font-['Roboto'] text-6xl font-normal leading-[66px] text-white tablet:w-[378px]">
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
