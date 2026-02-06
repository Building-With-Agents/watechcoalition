import { ReadEduProviderProgramCardDTO } from "@/app/lib/eduProviders";
import Image from "next/image";
import Link from "next/link";

export default async function TrainingProgramCard(
  program: ReadEduProviderProgramCardDTO,
) {
  // default to TWC if missing edu provider logo
  const logoURL = program.logoUrl || "/images/TWC_75x50_2024.svg";

  return (
    <div className="flex-col justify-start items-start inline-flex">
      <div className="flex-col justify-start items-start flex">
        <div className="group w-80 h-80 rounded-3xl flex-col justify-start items-start flex">
          <Link
            href={"/services/training-programs/" + program.programId}
            className="w-80"
          >
            <div className="self-stretch grow shrink basis-0 px-7 py-2 bg-neutral-100 text-sky-900 rounded-t-3xl flex-col justify-start items-start flex">
              {program.eduLevel && (
                <div className="mt-4 px-4 py-2 bg-cyan-700 rounded-full justify-center items-center gap-1 flex">
                  <div className="text-center text-white text-sm font-medium font-['Roboto'] capitalize leading-tight tracking-tight">
                    {program.eduLevel}
                  </div>
                </div>
              )}
              <div className="w-full justify-between items-start inline-flex">
                <Image
                  src={logoURL}
                  width={144}
                  height={144}
                  alt="Edu provider logo"
                  className="h-36 w-full object-contain"
                />
              </div>
            </div>
            <div className="group-hover:bg-sky-900 group-hover:text-neutral-100 self-stretch grow shrink basis-0 px-6 py-2 bg-neutral-100 text-sky-900 rounded-b-3xl flex-col justify-start items-start flex">
              <div className="line-clamp-1 self-stretch text-2xl font-normal font-['Roboto']">
                {program.programName}
              </div>
              <div className="mt-2 self-stretch justify-start items-start gap-2.5 inline-flex">
                <div className="line-clamp-1 text-cyan-600 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                  {program.eduProviderName}
                  {program.locationType && " | "}
                  {program.locationType}
                </div>
              </div>
              <div className="mt-2 self-stretch justify-start items-start gap-2.5 inline-flex">
                <div className="line-clamp-1 text-base font-normal font-['Roboto'] uppercase leading-none tracking-wider">
                  {program.programLength}
                  {program.programLength && " | "}
                  {program.tuition}
                  {program.tuition && " | "}
                  {program.fees}
                  {program.fees && " fee"}
                </div>
              </div>
            </div>
          </Link>
        </div>
      </div>
    </div>
  );
}
