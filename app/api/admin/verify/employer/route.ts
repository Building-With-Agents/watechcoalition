import { adminEmployerApproval } from "@/app/lib/admin/companyManagement";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body: { employerId: string; isVerified: boolean } = await req.json();
  const res = await adminEmployerApproval(body.employerId, body.isVerified);
  if (res) {
    return NextResponse.json(res, { status: 200 });
  } else {
    return NextResponse.json({}, { status: 500 });
  }
}
