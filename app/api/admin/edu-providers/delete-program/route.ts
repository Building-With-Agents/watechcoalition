import { deleteProviderProgram } from "@/app/lib/admin/eduProviderPartner";
import { NextResponse } from "next/server";

export async function DELETE(req: Request) {
  const body: { provider_program_id: string } = await req.json();
  try {
    const res = await deleteProviderProgram(body.provider_program_id);
    if (res) {
      return NextResponse.json(res);
    } else {
      return NextResponse.json({ res }, { status: 500 });
    }
  } catch {
    return NextResponse.json({}, { status: 500 });
  }
}
