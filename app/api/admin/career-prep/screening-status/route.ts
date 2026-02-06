import { setPresreenedStatus } from "@/app/lib/admin/careerPrep";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const body: { jobseekerId: string; prescreened: boolean } = await req.json();
  const res = await setPresreenedStatus(body.jobseekerId, body.prescreened);
  if (res) {
    return NextResponse.json(res);
  } else {
    return NextResponse.json({ Message: "failed" }, { status: 500 });
  }
}
