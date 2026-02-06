import { adminCreateCompany } from "@/app/lib/admin/companyManagement";
import { CompanyAdminCreationDTO } from "@/data/dtos/CompanyAdminCreationDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body: CompanyAdminCreationDTO = await req.json();
    console.log("Request body:", body);
    const result = await adminCreateCompany(body);
    return NextResponse.json(result);
  } catch (error) {
    console.error("Error in POST handler:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 },
    );
  }
}
