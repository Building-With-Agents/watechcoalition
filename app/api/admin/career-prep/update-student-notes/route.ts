import {
  updateCareerPrepStudentNotes,
  UpdateNoteDTO,
} from "@/app/lib/admin/careerPrep";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { NextResponse } from "next/server";
//
export async function POST(req: Request) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.CASE_MANAGER) &&
    !session?.user.roles.includes(Role.ADMIN)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  const body: UpdateNoteDTO = await req.json();
  return NextResponse.json(
    await updateCareerPrepStudentNotes(
      body.noteId,
      body.noteContent,
      body.noteType,
      body.updatedDate ? body.updatedDate : new Date(),
    ),
  );
}
