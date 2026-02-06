import RoundedButton from "../RoundedButton";
import Image from "next/image";
import AvatarClusterImg from "./AvatarCluster.png";
export default async function BottomFold() {
  return (
    <div className="bg-blue-textdark2 py-20 px-4 tablet:px-[150px] laptop:px-[200px] laptop:grid laptop:grid-cols-2 laptop:place-items-center laptop:gap-[32px]">
      <div className="space-y-[32px]">
        <h4 className="text-white text-6xl">
          Ready to Find Your Next Tech Hire?
        </h4>
        <RoundedButton content={"Get Started today"} invertColor={false} />
      </div>
      <Image
        className="w-[450px] hidden laptop:block"
        src={AvatarClusterImg}
        alt="A cluster of profile pictures"
      />
    </div>
  );
}
