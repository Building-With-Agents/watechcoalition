import { getSkillsFromList } from "@/app/lib/prisma";

export async function GET(
  req: Request,
  props: { params: Promise<{ names: string }> },
) {
  const params = await props.params;
  const skillNames = params.names
    .split(",")
    .map((skillName) => decodeURIComponent(skillName));
  const skills = await getSkillsFromList(skillNames);

  return Response.json(skills, {
    status: 200,
  });
}
