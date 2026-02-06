import { NextResponse } from "next/server";
import { deleteEmployerWithSession } from "@/app/lib/employer";

export async function DELETE() {
  try {
    // Call deleteEmployer and wait for its resolution
    await deleteEmployerWithSession();
    // If successful, return a success response
    return NextResponse.json(
      { success: true, message: "Employer deleted successfully." },
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
