import { createCompany } from "@/app/lib/employer";
import { CompanyEmployerCreationDTO } from "@/data/dtos/CompanyEmployerCreateionDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body: CompanyEmployerCreationDTO = await req.json();
  console.log("Request body:", body);
  const result = await createCompany(body);
  return NextResponse.json(result);
}
