import { deleteEduProvider } from "@/app/lib/admin/eduProviderPartner";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";
/**
 * not implemented yet
 * @returns
 */
export async function DELETE(req: Request) {
  const session = await auth();
  const body: { providerId: string } = await req.json();
  if (!session?.user.roles.includes(Role.ADMIN)) {
    return NextResponse.json({}, { status: 401 });
  }
  const result = await deleteEduProvider(body.providerId);
  return NextResponse.json(result);
}
