import { NextResponse } from "next/server"; // Adjust imports based on your framework
import { getProviderProgramByProvider } from "@/app/lib/admin/eduProviderPartner";
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
    const trainingProvider = await getProviderProgramByProvider(eduProviderId);

    if (!trainingProvider) {
      return NextResponse.json(
        { error: "Education provider not found" },
        { status: 404 },
      );
    }

    return NextResponse.json(trainingProvider, { status: 200 });
  } catch (error) {
    console.error("Error fetching education provider:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
