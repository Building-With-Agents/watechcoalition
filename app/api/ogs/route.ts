import { NextResponse } from "next/server";
import ogs from "open-graph-scraper";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const url = searchParams.get("url");
  if (!url || typeof url !== "string") {
    return NextResponse.json({ error: "Invalid URL" }, { status: 400 });
  }

  try {
    const options = { url: url, timeout: 4 };
    const result = await ogs(options);
    const ogImage = result.result.ogImage?.[0]?.url;
    return NextResponse.json({ image: ogImage });
  } catch (error) {
    console.error("Error fetching OG image:", error);
    return NextResponse.json(
      { error: `Error fetching image: ${error}` },
      { status: 500 },
    );
  }
}
