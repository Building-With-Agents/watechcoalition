import { NextResponse } from "next/server"; // Adjust imports based on your framework
import { getProviderProgramCardView } from "@/app/lib/eduProviders";
export async function GET(
  request: Request,
  props: { params: Promise<{ eduProviderId: string }> },
) {
  const params = await props.params;
  const eduProviderId = params.eduProviderId;

  if (!eduProviderId) {
    return NextResponse.json(
      { error: "eduProviderId is required" },
      { status: 400 },
    );
  }

  try {
    const providerPrograms = await getProviderProgramCardView(eduProviderId);

    if (!providerPrograms) {
      return NextResponse.json(
        { error: "Training provider programs not found." },
        { status: 404 },
      );
    }

    return NextResponse.json(providerPrograms, { status: 200 });
  } catch (error) {
    console.error("Error fetching training provider programs:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
