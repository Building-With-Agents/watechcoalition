import { updateCompany } from "@/app/lib/employer";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";
import { companies } from "@prisma/client";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const session = await auth();
  if (
    !session?.user.roles.includes(Role.ADMIN) &&
    !session?.user.roles.includes(Role.CASE_MANAGER)
  ) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }
  try {
    const body: companies = await req.json();
    if (body.estimated_annual_hires) {
      body.estimated_annual_hires = parseInt(
        body.estimated_annual_hires as unknown as string,
        10,
      );
    }
    if (body.year_founded) {
      body.year_founded = parseInt(body.year_founded as unknown as string);
    }
    // Log the parsed body to ensure it's as expected
    console.log("Parsed body:", body);

    // Validate company_id exists and is in the correct format
    if (!body.company_id) {
      return NextResponse.json(
        { msg: "company_id is required" },
        { status: 400 },
      );
    }

    // Optionally, check for proper company_id format (e.g., UUID format)
    const companyIdPattern =
      /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    if (!companyIdPattern.test(body.company_id)) {
      return NextResponse.json(
        { msg: "Invalid company_id format" },
        { status: 400 },
      );
    }

    if (!body || Object.keys(body).length === 0) {
      return NextResponse.json(
        { msg: "Invalid or empty data received" },
        { status: 400 },
      );
    }

    const res = await updateCompany(body);

    if (res) {
      return NextResponse.json(res);
    } else {
      // Detailed error message
      return NextResponse.json(
        { msg: "Failed to update company. No data returned from update." },
        { status: 500 },
      );
    }
  } catch (error) {
    console.error("Error in POST handler:", error);
    return NextResponse.json({ msg: "Internal Server Error" }, { status: 500 });
  }
}
