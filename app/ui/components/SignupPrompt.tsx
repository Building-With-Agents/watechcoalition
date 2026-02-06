"use client";
import Link from "next/link";
import Image from "next/image";

interface Props {
  className?: string;
  vectorImgSrc: string;
  prompt?: string;
}

export default function SignupPrompt({
  className = "",
  vectorImgSrc,
  prompt,
}: Props) {
  return (
    <section
      className={
        "flex h-full w-full flex-col justify-between px-8 laptop:bg-gray-50 laptop:pt-28 laptop:text-center" +
        className
      }
    >
      <div className="mx-auto flex flex-col gap-4 py-4 laptop:max-w-[390px] laptop:gap-6">
        <h1 className="text-center text-[34px] leading-[42px]">
          Create a TWC account
        </h1>
        <p className="">{prompt}</p>
        <div className="hidden py-4 laptop:block">
          <p>Not ready to log in?</p>
          <p>
            <Link target="_blank" href="/about-us" className="underline">
              Learn how TWC works
            </Link>
          </p>
        </div>
      </div>
      <Image
        src={vectorImgSrc}
        width={1092}
        height={1040}
        className="my-auto hidden h-1/2 w-full object-contain laptop:block"
        alt="Art of jobseeker"
      />
    </section>
  );
}
