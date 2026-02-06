import { deleteJobListing } from "@/app/lib/joblistings";
import { NextResponse } from "next/server";

export async function DELETE(
  request: Request,
  props: { params: Promise<{ id: string }> },
) {
  const params = await props.params;
  console.log("Delete: ", params.id);
  return NextResponse.json(await deleteJobListing(params.id));
}
