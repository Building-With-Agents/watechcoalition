import { EduProviderPathways } from "@/app/lib/eduProviders";
import Image from "next/image";

export default async function CareerPage({
  title,
  subtitle,
  img,
  altCareerNames,
  avgSalary,
  trainingLength,
  prepLevel,
  description,
  whatYoullDo,
  skillsYoullNeed,
  whyItMatters,
}: {
  title: string;
  subtitle: string;
  img: string;
  altCareerNames: string;
  avgSalary: string;
  trainingLength: string;
  prepLevel: string;
  description: string;
  whatYoullDo: string;
  skillsYoullNeed: string;
  whyItMatters: string;
  trainingPrograms: EduProviderPathways;
}) {
  // const programs: ReadEduProviderProgramCardDTO[] =
  //   await getProviderProgramCardView(trainingPrograms);

  return (
    <div className="w-full bg-neutral-100 flex-col justify-start items-center inline-flex">
      {/* Top card */}
      <div className="w-full bg-white">
        <div className="px-8 laptop:px-24 py-8 bg-white flex-col justify-start items-start gap-2.5 flex">
          <div className="bg-sky-900 rounded-2xl justify-start items-center inline-flex">
            <Image
              src={img}
              width={575}
              height={384}
              alt="Stock photo"
              className="hidden laptop:block h-96 rounded-tl-2xl rounded-bl-2xl"
            />
            <div className="grow shrink basis-0 p-6 flex-col justify-center items-start gap-2.5 inline-flex">
              <div className="text-neutral-100 text-5xl font-medium font-['Roboto'] leading-10">
                {title}
              </div>
              <div className="text-sky-200 text-3xl font-normal font-['Roboto'] capitalize leading-10">
                {subtitle}
              </div>
              <div className="flex-col justify-start items-start flex">
                <div className="w-px h-10 relative" />
              </div>
              <div className="text-white text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                Alternative career names
              </div>
              <div className="text-white/70 text-base font-normal font-['Roboto'] leading-snug">
                {altCareerNames}
              </div>
            </div>
          </div>
        </div>
      </div>
      {/* Quick facts cards */}
      <div className="py-8 justify-center items-start gap-2.5 inline-flex">
        <div className="px-5 py-4 bg-sky-200 rounded-2xl flex-col justify-start items-center gap-2.5 inline-flex">
          <div className="justify-center items-center gap-2 inline-flex">
            <div className="w-7 h-7 relative">
              <Image
                src="\images\careers\currency-dollar-circle.svg"
                height={28}
                width={28}
                alt="Dollar sign"
                className="w-7 h-7 left-0 top-0 absolute"
              />
            </div>
            <div className="text-sky-900 text-xl font-normal font-['Roboto'] capitalize leading-loose">
              {avgSalary}
            </div>
          </div>
          <div className="text-cyan-700 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
            Average Salary
          </div>
        </div>
        <div className="px-5 py-4 bg-sky-200 rounded-2xl flex-col justify-start items-center gap-2.5 inline-flex">
          <div className="justify-center items-center gap-2 inline-flex">
            <div className="w-7 h-7 relative">
              <Image
                src="\images\careers\clock-check.svg"
                height={28}
                width={28}
                alt="Clock symbol"
                className="w-7 h-7 left-0 top-0 absolute"
              />
            </div>
            <div className="text-sky-900 text-xl font-normal font-['Roboto'] capitalize leading-loose">
              {trainingLength}
            </div>
          </div>
          <div className="text-cyan-700 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
            Training Program
          </div>
        </div>
        <div className="px-5 py-4 bg-sky-200 rounded-2xl flex-col justify-start items-center gap-2.5 inline-flex">
          <div className="justify-center items-center gap-2 inline-flex">
            <div className="w-7 h-7 relative">
              <Image
                src="\images\careers\file-06.svg"
                height={28}
                width={28}
                alt="File symbol"
                className="w-7 h-7 left-0 top-0 absolute"
              />
            </div>
            <div className="text-sky-900 text-xl font-normal font-['Roboto'] capitalize leading-loose">
              {prepLevel}
            </div>
          </div>
          <div className="text-cyan-700 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
            Preparation level
          </div>
        </div>
      </div>
      <div className="w-full px-8 bg-white flex-col justify-start items-center gap-2.5 flex">
        <div className="flex-col justify-start items-start flex">
          <div className="w-px h-10 relative" />
        </div>
        {/* Description */}
        <div className="flex-col justify-center items-center gap-2.5 flex">
          <div className="text-sky-900 text-3xl font-normal font-['Roboto'] leading-10">
            {description}
          </div>
          <div className="flex-col justify-start items-start flex">
            <div className="w-px h-10 relative" />
          </div>
          {/* Quick descriptions */}
          <div className="flex flex-row flex-wrap justify-center items-center gap-2.5">
            <div className="w-96 flex-col justify-center items-center gap-2.5 inline-flex">
              <div className="text-center text-cyan-600 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                WHAT you’ll do
              </div>
              <div className="text-center text-zinc-900 text-base font-normal font-['Roboto'] leading-snug">
                {whatYoullDo}
              </div>
            </div>
            <div className="w-96 flex-col justify-center items-center gap-2.5 inline-flex">
              <div className="text-center text-cyan-600 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                Skills you’ll need
              </div>
              <div className="text-center text-zinc-900 text-base font-normal font-['Roboto'] leading-snug">
                {skillsYoullNeed}
              </div>
            </div>
            <div className="w-96 flex-col justify-center items-center gap-2.5 inline-flex">
              <div className="text-center text-cyan-600 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">
                Why it matters
              </div>
              <div className="text-center text-zinc-900 text-base font-normal font-['Roboto'] leading-snug">
                {whyItMatters}
              </div>
            </div>
          </div>
        </div>
        <div className="flex-col justify-start items-start flex">
          <div className="w-px h-10 relative" />
        </div>
        {/*<div className="h-96 px-24 py-4 rounded-3xl flex-col justify-center items-start gap-2.5 flex">*/}
        {/*    <div className="text-sky-900 text-3xl font-medium font-['Roboto'] leading-10">Local Wage Data</div>*/}
        {/*    <div className="justify-start items-center inline-flex">*/}
        {/*        <div className="w-72 py-4 rounded-tl-3xl rounded-bl-3xl flex-col justify-start items-start gap-2 inline-flex">*/}
        {/*            <div className="p-5 bg-sky-200 rounded-tl-lg rounded-bl-lg justify-center items-center gap-4 inline-flex">*/}
        {/*                <div className="text-sky-900 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">key data points</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tl-lg rounded-bl-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-cyan-700 text-base font-normal font-['Roboto'] leading-snug">Average Salary</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tl-lg rounded-bl-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-cyan-700 text-base font-normal font-['Roboto'] leading-snug">Education Level</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tl-lg rounded-bl-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-cyan-700 text-base font-normal font-['Roboto'] leading-snug">Experience Requirements</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tl-lg rounded-bl-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-cyan-700 text-base font-normal font-['Roboto'] leading-snug">Job Growth Rate</div>*/}
        {/*            </div>*/}
        {/*        </div>*/}
        {/*        <div className="grow shrink basis-0 py-4 rounded-tr-3xl rounded-br-3xl flex-col justify-start items-start gap-2 inline-flex">*/}
        {/*            <div className="p-5 bg-sky-200 rounded-tr-lg rounded-br-lg justify-center items-center gap-4 inline-flex">*/}
        {/*                <div className="text-sky-900 text-base font-semibold font-['Roboto'] uppercase leading-none tracking-wider">DETAILS</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tr-lg rounded-br-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-zinc-900 text-base font-normal font-['Roboto'] leading-snug">{tableAvgSalary}</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tr-lg rounded-br-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-zinc-900 text-base font-normal font-['Roboto'] leading-snug">{tableEduLevel}</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tr-lg rounded-br-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-zinc-900 text-base font-normal font-['Roboto'] leading-snug">{tableExpReq}</div>*/}
        {/*            </div>*/}
        {/*            <div className="p-5 bg-neutral-100 rounded-tr-lg rounded-br-lg justify-start items-center gap-4 inline-flex">*/}
        {/*                <div className="text-zinc-900 text-base font-normal font-['Roboto'] leading-snug">{tableJobGrowth}</div>*/}
        {/*            </div>*/}
        {/*        </div>*/}
        {/*    </div>*/}
        {/*    <div className="flex-col justify-start items-start flex">*/}
        {/*        <div className="w-px h-10 relative" />*/}
        {/*    </div>*/}
        {/*</div>*/}

        {/*<div className="w-full flex-col justify-center items-start gap-2.5 flex">*/}
        {/*  <div className="text-sky-900 text-3xl font-medium font-['Roboto'] leading-10">*/}
        {/*    Coalition Provider Training Programs*/}
        {/*  </div>*/}
        {/*  <div className="text-zinc-900 text-base font-normal font-['Roboto'] leading-tight">*/}
        {/*    Jumpstart your journey with hands-on, industry-aligned training.*/}
        {/*    These partner programs offer the skills, mentorship, and credentials*/}
        {/*    you need to succeed in your chosen tech career.*/}
        {/*  </div>*/}
        {/*  /!* <div className="justify-end items-start gap-2.5 inline-flex">*/}
        {/*                <div className="px-5 py-3 bg-neutral-100 rounded-full justify-center items-center gap-1.5 flex">*/}
        {/*                    <div className="text-center text-sky-900 text-base font-medium font-['Roboto'] capitalize leading-tight tracking-tight">See More</div>*/}
        {/*                </div>*/}
        {/*            </div> *!/*/}
        {/*  <div className="flex-col justify-start items-start flex">*/}
        {/*    <div className="w-px h-2.5 relative" />*/}
        {/*  </div>*/}
        {/*  /!* <div className="w-full h-[22rem] justify-start items-start gap-4 inline-flex"> *!/*/}
        {/*  <div className="w-full pb-8 justify-center items-center gap-2 laptop:gap-10 inline-flex flex-wrap">*/}
        {/*    {programs.map(function (program) {*/}
        {/*      return TrainingProgramCard(program);*/}
        {/*    })}*/}
        {/*  </div>*/}
        {/*</div>*/}
      </div>
    </div>
  );
}
