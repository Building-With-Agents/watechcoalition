import { parseTextForSkills, vectorSearchSkills } from "@/app/lib/prisma";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  const body = await req.json();
  const { text } = body;

  let raw: string | null | undefined;
  try {
    raw = await parseTextForSkills(text);
  } catch (err: any) {
    const status = err?.status ?? err?.response?.status;
    const message = err?.message || "AI service error";

    // Best-effort retry-after extraction (Azure message often includes "retry after X seconds")
    const match =
      typeof message === "string"
        ? message.match(/retry after (\d+)\s*seconds/i)
        : null;
    const retryAfterSeconds = match ? Number(match[1]) : null;

    if (status === 429) {
      const headers: Record<string, string> = {};
      if (
        typeof retryAfterSeconds === "number" &&
        Number.isFinite(retryAfterSeconds)
      ) {
        headers["Retry-After"] = String(retryAfterSeconds);
      }
      return NextResponse.json(
        {
          message: "AI rate limit reached. Please retry shortly.",
          error: message,
          retryAfterSeconds,
        },
        { status: 429, headers },
      );
    }

    return NextResponse.json(
      { message: "AI service failed.", error: message },
      { status: 502 },
    );
  }
  if (!raw) {
    return NextResponse.json(
      { error: "Azure OpenAI returned an empty response." },
      { status: 502 },
    );
  }

  let parseResult: any;
  try {
    parseResult = JSON.parse(raw);
  } catch {
    return NextResponse.json(
      {
        error: "Azure OpenAI returned invalid JSON.",
        raw: raw.slice(0, 4000),
      },
      { status: 502 },
    );
  }

  const parsedSkills = parseResult.skills || [];
  if (parsedSkills.length === 0) {
    console.log("No skills parsed from text.");
    return NextResponse.json([]);
  }
  const searchPromises = parsedSkills.map(
    async (sk: {
      skillName: string;
      subcategory: string;
    }): Promise<SkillDTO | null> => {
      try {
        const searchResults: SkillDTO[] = await vectorSearchSkills(
          sk.skillName,
          1,
        );
        if (searchResults && searchResults.length > 0) {
          return searchResults[0];
        } else {
          return null;
        }
      } catch (searchError) {
        console.error(
          `Error during vector search for skill "${sk.skillName}":`,
          searchError,
        );
        return null;
      }
    },
  );
  const allSearchResults = await Promise.all(searchPromises);
  const topSkills: SkillDTO[] = allSearchResults.filter(
    (skill): skill is SkillDTO => skill !== null,
  );
  return NextResponse.json(topSkills);
}
