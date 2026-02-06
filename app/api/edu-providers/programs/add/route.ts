import {
  PostEduProviderProgramDetailDTO,
  upsertTrainingProviderProgram,
} from "@/app/lib/eduProviders";
import { NextResponse } from "next/server";
import { devLog } from "@/app/lib/utils";

export async function POST(req: Request) {
  try {
    const body: PostEduProviderProgramDetailDTO = await req.json();
    devLog("api hit");
    devLog("api/edu-providers/programs/add invoked with:", body);
    const result = await upsertTrainingProviderProgram(body);
    return NextResponse.json(result, { status: 200 });
  } catch (err) {
    console.error("Error in upsert route:", err);
    return NextResponse.json({ error: String(err) }, { status: 500 });
  }
}
