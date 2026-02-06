"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

function SkipButton() {
  const currentPath = usePathname(); //returns full path ie: /edit-profile/jobseeker/introduction
  // Early return if currentPath is null or undefined
  if (!currentPath) {
    return null;
  }
  let pageSequence: string[] = [];
  let userPrefix: string = "";
  if (currentPath.includes("/edit-profile/jobseeker")) {
    pageSequence = [
      "introduction",
      "preferences",
      "showcase",
      "education",
      "work-experience",
      "disclosures",
    ];
    userPrefix = "jobseeker";
  } else if (currentPath.includes("/edit-profile/employer")) {
    pageSequence = [
      "personal",
      // 'company',
      // 'about',
      // 'mission',
      // 'video',
      "disclosures",
    ];
    userPrefix = "employer";
  }
  const lastSegment = currentPath.split("/").pop() || ""; //returns last segment ie: introduction
  const currentIndex = pageSequence.indexOf(lastSegment);

  let nextPage =
    currentIndex >= 0 && currentIndex < pageSequence.length - 1
      ? `/edit-profile/${userPrefix}/${pageSequence[currentIndex + 1]}`
      : null;

  // hide skip button on jobseeker education and work exp pages, since we require this information
  if (
    nextPage === "/edit-profile/jobseeker/disclosures" ||
    nextPage === "/edit-profile/jobseeker/work-experience"
  ) {
    nextPage = null;
  }

  return nextPage ? (
    <Link
      href={nextPage}
      className="mt-1 inline-block h-fit rounded-full bg-cyan-700 px-4 py-2 text-white hover:bg-red-800"
    >
      Skip
    </Link>
  ) : null;
}

export default SkipButton;
