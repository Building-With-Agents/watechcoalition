import { deleteCareerPrepStudentNotes } from "@/app/lib/admin/careerPrep";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";

export async function DELETE(
  request: Request,
  props: { params: Promise<{ id: string }> },
) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const params = await props.params;
  console.log("Delete: ", params.id);

  return NextResponse.json(await deleteCareerPrepStudentNotes(params.id));
}
