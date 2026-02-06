import { adminUpdateCompanyApproval } from "@/app/lib/admin/companyManagement";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body: { companyId: string; isApproved: boolean } = await req.json();
  const res = await adminUpdateCompanyApproval(body.companyId, body.isApproved);
  if (res) {
    return NextResponse.json(res, { status: 200 });
  } else {
    return NextResponse.json({}, { status: 500 });
  }
}
