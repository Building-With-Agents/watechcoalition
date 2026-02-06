import { WarningAmberOutlined } from "@mui/icons-material";
import Link from "next/link";
import { PoolCategories } from "@/app/lib/poolAssignment";

export default async function CallToActionBanner({
  pool,
}: {
  pool: PoolCategories;
}) {
  let background = "";
  let copy =
    "Elevate your profile and stand out to Employers by completing your Career Prep track.";
  if (pool === PoolCategories.NotJobReady || pool === PoolCategories.None) {
    copy =
      "Your profile is currently not visible to employers based on your education and work experience. Complete Career Prep to become visible to employers.";
    background = "bg-[#da2627]";
  } else if (pool === PoolCategories.JobReady) {
    background = "bg-[#DF9C19]";
  } else if (PoolCategories.Recommended) {
    background = "bg-[#DF9C19]";
  }

  return (
    <div
      className={`w-full rounded-[10px] ${background} flex items-center gap-3 p-[20px] text-lg text-white`}
    >
      <WarningAmberOutlined />
      <div>
        <span className="font-bold">Attention </span>
        <span>{copy} </span>
        <Link
          href={"/services/jobseekers/career-prep/skill-assessment"}
          className="font-normal underline"
        >
          Take the Career Prep Skills Assessment.
        </Link>
      </div>
    </div>
  );
}
