"use client";
import Link from "next/link";
import Image from "next/image";
import Divider from "@mui/material/Divider";

export default function SignupHeader({ className }: { className?: string }) {
  return (
    <header className={"bg-white " + className}>
      <nav
        className="max-w-[theme(screens.lg)] w-full flex items-center justify-between py-6 laptop:px-8"
        aria-label="Global"
      >
        <div className="w-1/2">
          <Link href="/">
            <span className="sr-only">Tech Workforce Coalition</span>
            <Image
              src="/images/TWC_75x50_2024.svg"
              alt="Tech Workforce Coalition"
              width={75}
              height={50}
              priority
            />
          </Link>
        </div>
      </nav>
      <Divider className="hidden sm-tablet:block" />
    </header>
  );
}
