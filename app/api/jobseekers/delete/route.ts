import { NextResponse } from "next/server";
import { deleteJobseekerWithSession } from "@/app/lib/jobseeker";

export async function DELETE() {
  try {
    // Call deleteJobseeker and wait for its resolution
    await deleteJobseekerWithSession();
    // If successful, return a success response
    return NextResponse.json(
      { success: true, message: "Jobseeker deleted successfully." },
      { status: 200 },
    );
  } catch {
    // If an error occurs, return an error response with a 500 status code
    return NextResponse.json(
      { error: "Failed to delete jobseeker." },
      { status: 500 },
    );
  }
}
