import { searchEduProviderCollegePrograms } from "@/app/lib/prisma";

export async function GET(
  req: Request,
  props: { params: Promise<{ terms: string }> },
) {
  const params = await props.params;
  const terms = decodeURIComponent(params.terms);
  const searchResults = await searchEduProviderCollegePrograms(terms);

  return Response.json(searchResults, {
    status: 200,
  });
}
