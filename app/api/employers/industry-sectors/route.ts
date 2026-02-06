import { getIndustrySectors } from "@/app/lib/prisma";

export async function GET() {
  const industrySectors = await getIndustrySectors();

  return Response.json(industrySectors, {
    status: 200,
  });
}
