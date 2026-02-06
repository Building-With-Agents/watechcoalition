import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { PrismaClient } from "@prisma/client";
const prisma: PrismaClient = getPrismaClient();

export async function GET(
  req: Request,
  props: { params: Promise<{ terms: string }> },
) {
  const params = await props.params;
  const terms = decodeURIComponent(params.terms);
  const cities = await prisma.postalGeoData.findMany({
    where: { city: { contains: terms }, stateCode: "WA" },
    distinct: ["city"],
    take: 5,
    select: { city: true },
  });

  return Response.json(cities, {
    status: 200,
  });
}
