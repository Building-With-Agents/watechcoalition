"use client";
import Link from "next/link";
import Avatar from "../Avatar";
export default function EmployerNameTitleTag(props: {
  name: string | null | undefined;
  title: string;
  company: string;
  pfp: string | undefined;
}) {
  return (
    <div className="flex h-[76px] p-[16px] w-full items-center rounded-lg border p-4 bg-white rounded-[10px] shadow-xs grow">
      <Avatar imgsrc={props.pfp} scale={0.69} />
      <div className="flex w-full flex-wrap items-center justify-between p-4">
        <h2 className="font-bold">
          {props.name} | {props.title} |
          <span className="font-light"> {props.company}</span>
        </h2>
        <p>
          <Link
            className="text-[#1e88e5]"
            href="/edit-profile/employer/profile"
          >
            Edit My Profile
          </Link>{" "}
          {/* |{' '}
          <Link
            className="text-red-600"
            href="/underconstruction"
          >
            Edit Company Profile
          </Link> */}
        </p>
      </div>
    </div>
  );
}
