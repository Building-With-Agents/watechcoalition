import { searchSocc } from "@/app/lib/prisma";

export async function GET(
  req: Request,
  props: { params: Promise<{ term: string }> },
) {
  const params = await props.params;
  const term = decodeURIComponent(params.term);
  const searchResults = await searchSocc(term);

  return Response.json(searchResults, {
    status: 200,
  });
}
