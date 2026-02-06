import { getAllCities } from "@/app/lib/prisma";

export async function GET() {
  const cities = await getAllCities();
  return Response.json(cities, {
    status: 200,
  });
}
