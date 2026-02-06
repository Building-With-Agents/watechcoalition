import Link from "next/link";
import Image from "next/image";
import {
  getAllEduProvidersDetail,
  ReadEduProviderDTO,
} from "@/app/lib/eduProviders";
import RoundedButton from "./RoundedButton";

export default async function TrainingProviderMembers() {
  const trainingProviders: ReadEduProviderDTO[] | null =
    await getAllEduProvidersDetail();

  return (
    <div className="w-full py-4 flex-col justify-center items-center gap-5 inline-flex">
      <div className="mt-8 self-stretch text-center text-sky-900 text-xl font-semibold font-['Roboto'] uppercase leading-loose tracking-widest">
        Coalition Training Provider Members
      </div>
      <div className="w-full pb-8 justify-center items-center gap-10 inline-flex flex-wrap">
        {trainingProviders != null &&
          trainingProviders.map(function (tp, i) {
            return (
              <Link
                href={"/services/training-providers/" + tp.eduProviderId}
                key={i}
              >
                <div className="h-24 px-7 py-4 bg-neutral-100 hover:bg-sky-900 text-cyan-700 hover:text-neutral-100 rounded-3xl flex-col justify-start items-start gap-2.5 inline-flex">
                  <div className="self-stretch h-20 flex-col justify-center items-center gap-2.5 flex">
                    <div className="mt-2 self-stretch h-11 justify-center items-center gap-2.5 inline-flex">
                      <Image
                        width={500}
                        height={500}
                        className="w-32 h-20 object-contain"
                        src={tp.logoUrl || "/images/TWC_75x50_2024.svg"}
                        alt={tp.providerName + " logo"}
                      />
                    </div>
                    <div className="my-2 self-stretch justify-center items-center gap-2.5 inline-flex">
                      <div className="text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                        {tp.providerName}
                      </div>
                    </div>
                  </div>
                </div>
              </Link>
            );
          })}
      </div>
      <div className="pb-[34px] text-center">
        <RoundedButton
          content="Join the Coalition"
          link="/join"
          invertColor
          snug
          newColors
          bold={false}
          className="capitalize"
        />
      </div>
    </div>
  );
}
