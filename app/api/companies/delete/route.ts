import { adminDeleteCompany } from "@/app/lib/admin/companyManagement";
import { NextResponse } from "next/server";

export async function DELETE(req: Request) {
  try {
    // Parse and validate the request body
    const body: { companyId: string } = await req.json();
    if (!body.companyId) {
      console.error("Missing companyId in request body.");
      return NextResponse.json(
        { error: "companyId is required" },
        { status: 400 },
      );
    }
    const result = await adminDeleteCompany(body.companyId);

    if (result) {
      console.log("Company deleted successfully:", result);
      return NextResponse.json(result);
    } else {
      console.warn("Deletion was not successful or company was not found.");
      return NextResponse.json(
        { error: "Failed to delete company or company not found" },
        { status: 404 },
      );
    }
  } catch (error) {
    console.error("Error in DELETE handler:", error);
    return NextResponse.json(
      { error: "An error occurred while processing your request" },
      { status: 500 },
    );
  }
}
