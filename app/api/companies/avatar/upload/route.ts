import { NextResponse } from "next/server";
import { uploadAvatar } from "@/app/lib/services/azureBlobService";
import { auth } from "@/auth";
import { Role } from "@/data/dtos/UserInfoDTO";

export const config = {
  api: {
    bodyParser: {
      sizeLimit: "5mb",
    },
  },
};

export async function POST(request: Request) {
  try {
    const session = await auth();
    const employeeIsApproved: boolean =
      session?.user.employeeIsApproved || false;

    const body = await request.json();
    const { file, fileName, id } = body; // destructured userId from the body

    if (!file || !id) {
      return NextResponse.json(
        { success: false, error: "Missing file or companyId" },
        { status: 400 },
      );
    }

    if (!employeeIsApproved && !session?.user.roles.includes(Role.ADMIN)) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 },
      );
    }

    // Convert file back to Buffer
    const fileBuffer = Buffer.from(new Uint8Array(file));

    // Upload the image using the Azure Blob Storage service
    const imageUrl = await uploadAvatar(fileBuffer, fileName, id);

    return NextResponse.json({ success: true, imageUrl }, { status: 200 });
  } catch (e: any) {
    return NextResponse.json(
      { error: `Failed to upload image: ${e.message}` },
      { status: 500 },
    );
  }
}
