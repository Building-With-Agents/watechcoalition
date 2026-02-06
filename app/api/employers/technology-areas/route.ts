import { getTechnologyAreas } from "@/app/lib/prisma";

export async function GET() {
  const technologyAreas = await getTechnologyAreas();

  return Response.json(technologyAreas, {
    status: 200,
  });
}
