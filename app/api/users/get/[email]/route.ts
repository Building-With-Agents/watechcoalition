import { NextResponse } from "next/server";
import { getUserByEmail } from "@/app/lib/user";

export async function GET(
  request: Request,
  props: { params: Promise<{ email: string }> },
) {
  const params = await props.params;
  try {
    const { email } = params;
    const result = await getUserByEmail(email);

    if (!result) {
      return NextResponse.json(
        { success: false, error: `User not found.` },
        { status: 404 },
      );
    }

    return NextResponse.json({ success: true, result }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to read jobseeker skills: ${e.message}` },
      { status: 500 },
    );
  }
}
