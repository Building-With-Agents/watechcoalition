import { vectorSearchSkills } from "@/app/lib/prisma";
import { auth } from "@/auth";

export async function GET(
  req: Request,
  props: { params: Promise<{ terms: string }> },
) {
  const session = await auth();
  if (session) {
    const params = await props.params;
    const terms = decodeURIComponent(params.terms);
    const searchResults = await vectorSearchSkills(terms, 5);

    return Response.json(searchResults, {
      status: 200,
    });
  }
  return Response.json({
    status: 401,
  });
}
