"use client";
import Link from "next/link";
import Image from "next/image";
import SkipButton from "@/app/ui/components/SkipButton";

export default function ProfileCreationHeader() {
  return (
    <header className="bg-white">
      <nav
        className="mx-auto flex items-center justify-between p-6 laptop:px-8"
        aria-label="Global"
      >
        <div className="flex laptop:flex-1">
          <Link href="/">
            <span className="sr-only">Tech Workforce Coalition</span>
            <Image
              src="/images/TWC_75x50_2024.svg"
              alt="Tech Workforce Coalition"
              width={75}
              height={31.8}
            />
          </Link>
        </div>

        <div className="flex flex-1 justify-end">
          <SkipButton />
        </div>
      </nav>
    </header>
  );
}
