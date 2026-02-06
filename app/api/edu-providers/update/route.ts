import { NextResponse } from "next/server";
import {
  addTrainingPartner,
  AddTrainingPartnerDTO,
} from "@/app/lib/admin/eduProviderPartner";

export async function PATCH(req: Request) {
  try {
    const body: AddTrainingPartnerDTO = await req.json();
    console.log("Request body:", body);

    const result = await addTrainingPartner(body);

    // Clean up the result to ensure JSON serialization
    const serializableResult = JSON.parse(JSON.stringify(result));

    return NextResponse.json(serializableResult, { status: 200 });
  } catch (error) {
    console.error("Error in PATCH handler:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
