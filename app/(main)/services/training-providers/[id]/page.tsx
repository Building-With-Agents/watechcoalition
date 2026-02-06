import {
  EduProviderPathways,
  getEduProviderDetail,
  getProviderProgramCardView,
  ReadEduProviderDTO,
  ReadEduProviderProgramCardDTO,
} from "@/app/lib/eduProviders";
import TrainingProgramCard from "@/app/ui/components/career/TrainingProgramCard";
import Image from "next/image";
import Link from "next/link";

export default async function page(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const provider: ReadEduProviderDTO | null = await getEduProviderDetail(
    params.id,
  );
  const programs: ReadEduProviderProgramCardDTO[] =
    await getProviderProgramCardView(params.id);

  // Create a list of unique pathways this provider offers
  const careerPrograms: EduProviderPathways[] = [];
  programs.forEach((program) => {
    program.pathway.forEach((pathway) => {
      if (!careerPrograms.includes(pathway)) {
        careerPrograms.push(pathway);
      }
    });
  });

  return (
    <div className="px-8 sm-tablet:px-12 tablet:px-64 flex-col justify-start items-center gap-5 inline-flex">
      <div className="flex-col justify-start items-start flex">
        <div className="w-px h-10 relative" />
      </div>
      <div className="self-stretch flex-col justify-center items-start gap-6 flex">
        <div className="self-stretch justify-center items-center gap-10 inline-flex">
          <div className="hidden sm-tablet:block h-32 relative">
            <Image
              src="/images/landing/TWC-logo.svg"
              width={242}
              height={155}
              alt="TWC logo"
              className="w-52 h-32"
            />
          </div>
          {provider?.logoUrl && (
            <div className="hidden sm-tablet:block border-2 border-cyan-700 flex-col justify-start items-start inline-flex">
              <div className="w-[0px] h-20 relative" />
            </div>
          )}
          {provider?.logoUrl && (
            <Image
              src={provider?.logoUrl || ""}
              width={242}
              height={155}
              alt={provider?.providerName + " logo"}
              className="h-32 object-contain"
            />
          )}
        </div>
        {provider?.providerDescription && (
          <div className="mt-8 self-stretch text-sky-900 text-5xl font-normal font-['Roboto'] capitalize leading-10">
            Description
          </div>
        )}
        <div className="self-stretch">
          <span className="text-zinc-900 text-xl font-normal font-['Roboto'] leading-loose">
            {provider?.providerDescription}
          </span>
        </div>
      </div>
      <div className="flex-col justify-start items-start flex">
        <div className="w-px h-5 relative" />
      </div>
      <div className="self-stretch sm-tablet:px-12 flex-col justify-start items-center gap-5 flex">
        <div className="self-stretch flex-col justify-center items-start gap-2.5 flex">
          <div className="self-stretch">
            <span className="text-sky-900 text-3xl font-normal font-['Roboto'] leading-10">
              {provider?.mission}
            </span>
          </div>
          <div className="flex-col justify-start items-start flex">
            <div className="w-px h-10 relative" />
          </div>
          <div className="self-stretch text-center text-sky-900 text-3xl font-normal font-['Roboto'] leading-10 underline">
            <Link href={provider?.url || ""}>{provider?.url}</Link>
          </div>
          <div className="flex-col justify-start items-start flex">
            <div className="w-px h-10 relative" />
          </div>
          <div className="self-stretch justify-center items-start gap-2.5 inline-flex">
            <div className="w-full flex-col justify-start items-center gap-2.5 inline-flex">
              <div className="text-center text-cyan-600 text-xl font-semibold font-['Roboto'] uppercase leading-snug tracking-widest">
                Contact
              </div>
              <div className="self-stretch text-center text-zinc-900 text-xl font-normal font-['Roboto'] leading-loose">
                {provider?.contactName}
                <br />
                {provider?.contactEmail}
              </div>
            </div>
            <div className="w-full flex-col justify-start items-center gap-2.5 inline-flex">
              <div className="text-cyan-600 text-xl font-semibold font-['Roboto'] uppercase leading-snug tracking-widest">
                Career programs
              </div>
              <div className="whitespace-pre-wrap self-stretch text-center text-zinc-900 text-xl font-normal font-['Roboto'] leading-loose">
                {careerPrograms.join("\n")}
              </div>
            </div>
          </div>
        </div>
        <div className="flex-col justify-start items-start flex">
          <div className="w-px h-5 relative" />
        </div>
        <div className="mt-12 self-stretch flex-col justify-center items-start gap-6 flex">
          <div className="text-sky-900 text-3xl font-normal font-['Roboto'] leading-10">
            Provider Training Programs
          </div>
          <div className="self-stretch">
            <span className="text-zinc-900 text-xl font-normal font-['Roboto'] leading-relaxed">
              {provider?.setsApartStatement}
            </span>
          </div>
          <div className="flex-col justify-start items-start flex">
            <div className="w-px h-5 relative" />
          </div>
          <div className="w-full pb-8 justify-center items-center gap-2 laptop:gap-10 inline-flex flex-wrap">
            {programs.map(function (program) {
              return TrainingProgramCard(program);
            })}
          </div>
        </div>
      </div>
      <div className="flex-col justify-start items-start flex">
        <div className="w-px h-5 relative" />
      </div>
    </div>
  );
}
