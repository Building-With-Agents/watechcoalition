"use client";
import Link from "next/link";
import ArrowForwardIcon from "@mui/icons-material/ArrowForward";
export default function GreenMarketingBanner(props: { show: boolean }) {
  return (
    <div
      className={
        "bg-green-700 min-h-[60px] flex flex-wrap items-center sm-tablet:justify-center px-4 text-white " +
        (props.show ? "" : " hidden")
      }
    >
      <p className="mr-2">🔥 Explore our new Talent Portal release 1.4</p>
      <Link href="/signin" className="underline hover:text-gray-200">
        Create an account or log in <ArrowForwardIcon />
      </Link>
    </div>
  );
}
