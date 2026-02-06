import "@/app/ui/admin.css";
import Link from "next/link";
import PersonOutlineOutlinedIcon from "@mui/icons-material/PersonOutlineOutlined";
import ManageAccountsOutlinedIcon from "@mui/icons-material/ManageAccountsOutlined";
import { auth } from "@/auth";
import { PencilSquareIcon } from "@heroicons/react/24/outline";
import ApprovalOutlinedIcon from "@mui/icons-material/ApprovalOutlined";
import {
  AddBusinessOutlined,
  PsychologyOutlined,
  Science,
} from "@mui/icons-material";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
export default async function layout({
  children,
}: {
  children: React.ReactNode;
}) {
  const session = await auth();
  console.log(session);

  return (
    <div className="flex capitalize">
      <div className="flex min-w-[230px] flex-col text-primary-main">
        <Link
          href="/admin"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <PersonOutlineOutlinedIcon />
          Home
        </Link>
        <Link
          href="/admin/generate-embeddings"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <Science />
          Generate Embeddings
        </Link>
        <Link
          href="/admin/add-edu-provider"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <AddBusinessOutlined />
          Add Training Provider
        </Link>
        <Link
          href="/admin/update-edu-provider"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <AddBusinessOutlined />
          Update Training Provider
        </Link>
        <Link
          href="/admin/add-company"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <AddBusinessOutlined />
          Add a Company
        </Link>
        <Link
          href="/admin/update-company"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <AddBusinessOutlined />
          Update Company
        </Link>
        <Link
          href="/admin/add-skill"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <PsychologyOutlined />
          Add Skill
        </Link>
        <Link
          href="/admin/update-skill"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <PsychologyOutlined />
          Update Skill
        </Link>
        <Link
          href="/admin/verify"
          className="inline-flex items-center justify-start gap-[5px] p-2 hover:bg-gray-200"
        >
          <ApprovalOutlinedIcon />
          Verify
        </Link>
        <Link
          href="/admin/user-management"
          className="inline-flex items-center justify-start gap-[5px]  p-2 hover:bg-gray-200"
        >
          <ManageAccountsOutlinedIcon />
          User Management
        </Link>
        <Link
          href="/admin/postjob"
          className="inline-flex items-center justify-start gap-[5px]  p-2 hover:bg-gray-200"
        >
          <PencilSquareIcon width={24} />
          Post a job
        </Link>
        <Link
          href="/admin/updatejob"
          className="inline-flex items-center justify-start gap-[5px]  p-2 hover:bg-gray-200"
        >
          <UpdateOutlinedIcon />
          Update a job
        </Link>
      </div>
      {children}
    </div>
  );
}
