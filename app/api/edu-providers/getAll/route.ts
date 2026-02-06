import { getTrainingProviders } from "@/app/lib/prisma";

export async function GET() {
  const trainingProviders = await getTrainingProviders();
  return Response.json(trainingProviders, {
    status: 200,
  });
}
