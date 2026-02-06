import {
  getProviderProgramDetailView,
  ReadEduProviderProgramDetailDTO,
} from "@/app/lib/eduProviders";
import Image from "next/image";
import Link from "next/link";

export default async function page(props: { params: Promise<{ id: string }> }) {
  const params = await props.params;
  const trainingProgramDetails: ReadEduProviderProgramDetailDTO =
    await getProviderProgramDetailView(params.id);

  // default to TWC if missing edu provider logo
  const logoURL =
    trainingProgramDetails.logoUrl || "/images/TWC logo_White.svg";

  return (
    <div className="w-full bg-white flex-col justify-start items-start inline-flex">
      <div className="pt-32 self-stretch px-6 laptop:px-24 py-8 bg-linear-to-b from-blue-700 to-blue-600 justify-start items-center gap-2.5 inline-flex">
        <div className="w-full laptop:w-2/3 rounded-2xl flex-col justify-end items-start inline-flex">
          <div className="h-64 flex-col justify-center items-start gap-2.5 flex">
            {/* Edu Provider Logo */}
            <Image
              src={logoURL}
              width={256}
              height={256}
              alt="Edu provider logo"
              className="object-contain mb-4"
            />
            <div className="text-neutral-100 text-5xl font-medium leading-10">
              {trainingProgramDetails.programName}
            </div>
            <div className="text-sky-200 text-3xl font-normal capitalize leading-10">
              {trainingProgramDetails.eduProviderName}
            </div>
            <div className="flex-col justify-start items-start flex">
              <div className="w-px h-10 relative" />
            </div>
            {trainingProgramDetails.locations.map(function (loc, i) {
              return (
                <div
                  className="px-4 py-2.5 bg-cyan-700 rounded-full justify-center items-center gap-1 inline-flex"
                  key={i}
                >
                  <div className="w-4 h-4 relative">
                    <Image
                      src="/images/careers/marker-pin-01.svg"
                      width={16}
                      height={16}
                      alt="Pin icon"
                      className="w-4 h-4 left-0 top-0 absolute"
                    />
                  </div>
                  <div className="text-center text-white text-sm font-medium capitalize leading-tight tracking-tight">
                    {loc}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      <div className="w-full p-6 laptop:w-2/3 laptop:pl-32 laptop:pr-24 bg-white flex-col justify-start items-start gap-2.5 flex">
        <div className="self-stretch flex-col justify-center items-start gap-2.5 flex">
          {/* Quick Info */}
          <div className="mb-8 p-6 laptop:w-1/3 laptop:p-12 laptop:mr-8 laptop:right-[0px] laptop:top-[119px] laptop:fixed bg-blue-600 rounded-3xl flex-col justify-center items-center gap-2.5 flex">
            <div className="self-stretch flex-col justify-start items-center gap-2.5 flex">
              <div className="self-stretch leading-none text-neutral-100 text-5xl font-normal leading-10">
                Quick Information
              </div>
            </div>
            <div className="flex-col justify-start items-start flex">
              <div className="w-px h-5 relative" />
            </div>
            <div className="self-stretch flex-col justify-start items-start gap-2.5 flex">
              <div className="text-sky-200 text-base font-semibold uppercase leading-none tracking-wider">
                Cost
              </div>
              <div className="self-stretch">
                <span className="text-neutral-100 text-base font-semibold leading-snug">
                  Tuition:{" "}
                </span>
                <span className="text-neutral-100 text-base font-normal leading-snug">
                  {trainingProgramDetails.tuition}
                </span>
              </div>
              <div className="self-stretch">
                <span className="text-neutral-100 text-base font-semibold leading-snug">
                  Fees:{" "}
                </span>
                <span className="text-neutral-100 text-base font-normal leading-snug">
                  {trainingProgramDetails.fees}
                </span>
              </div>
              <div className="self-stretch">
                <span className="text-neutral-100 text-base font-normal leading-snug">
                  {trainingProgramDetails.costSummary}
                </span>
              </div>
              <div className="flex-col justify-start items-start flex">
                <div className="w-px h-2.5 relative" />
              </div>
              <div className="text-sky-200 text-base font-semibold uppercase leading-none tracking-wider">
                type of instruction
              </div>
              <div className="self-stretch text-neutral-100 text-base font-normal leading-snug">
                {trainingProgramDetails.locationType}
              </div>
            </div>
            <div className="flex-col justify-start items-start flex">
              <div className="w-px h-5 relative" />
            </div>
            <div className="px-5 py-3 bg-neutral-100 rounded-full justify-center items-center gap-1.5 inline-flex">
              <div className="text-center text-sky-900 text-base font-medium capitalize leading-tight tracking-tight">
                <Link
                  href={trainingProgramDetails.getStartedUrl}
                  target="_blank"
                >
                  Get Started
                </Link>
              </div>
            </div>
          </div>

          {/* About Section */}
          <div className="self-stretch flex-col justify-start items-start gap-2.5 flex">
            <div className="text-sky-900 text-3xl font-medium leading-10">
              {trainingProgramDetails.about && "About"}
            </div>
            <div className="self-stretch">
              <span className="text-zinc-900 text-base font-normal leading-tight">
                {trainingProgramDetails.about}
              </span>
            </div>
          </div>
          <div className="flex-col justify-start items-start flex">
            <div className="w-px h-2.5 relative" />
          </div>

          {/* FAQ's */}
          <div className="self-stretch flex-col justify-center items-start flex">
            <div className="text-sky-900 text-3xl font-medium leading-10">
              {trainingProgramDetails.faq.length > 0 ? "FAQ’s" : ""}
            </div>

            {trainingProgramDetails.faq.map(function (faq, i) {
              return (
                <div
                  className="self-stretch pt-4 rounded-3xl flex-col justify-start items-start gap-2 flex"
                  key={i}
                >
                  <div className="self-stretch p-5 bg-sky-200 rounded-lg justify-between items-center inline-flex">
                    <div className="text-sky-900 text-base font-medium leading-none">
                      {faq.question}
                    </div>
                    <div className="w-5 h-5 relative">
                      <div className="w-5 h-5 left-0 top-0 absolute" />
                    </div>
                  </div>
                  <div className="self-stretch px-11 py-5 bg-neutral-100 rounded-lg flex-col justify-center items-start gap-4 flex">
                    <div className="self-stretch text-zinc-900 text-base font-normal leading-snug">
                      {faq.answer}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex-col justify-start items-start flex">
            <div className="w-px h-2.5 relative" />
          </div>
        </div>
        <div className="flex-col justify-start items-start flex">
          <div className="w-px h-20 relative" />
        </div>
      </div>
    </div>
  );
}
