"use client";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { Chip, ChipProps, Grid } from "@mui/material";
import Link from "next/link";

export default function Skills({
  skillsList,
  maxNumSkills,
  jobseekerID,
  color = "primary",
}: {
  skillsList?: SkillDTO[];
  maxNumSkills: number;
  jobseekerID?: string;
  color?: ChipProps["color"];
}) {
  if (skillsList == null || skillsList.length == 0) return;

  let leftoverSkillsCount = 0;
  if (
    maxNumSkills != 0 && // 0 indicates show all skills
    skillsList.length > maxNumSkills
  ) {
    // avoid a leftover of "+1" skill
    leftoverSkillsCount = skillsList.length - maxNumSkills + 1;
    skillsList = skillsList.slice(0, maxNumSkills - 1);
  }

  return (
    <Grid container gap={1}>
      {skillsList.map((skill) =>
        skill?.skill_info_url.length > 0 ? (
          <Chip
            component={Link}
            clickable
            onClick={() => {}}
            color={color}
            key={skill?.skill_id}
            label={skill?.skill_name}
            target="_blank"
            href={skill?.skill_info_url}
          />
        ) : (
          <Chip
            clickable={false}
            onClick={() => {}}
            color={color}
            key={skill?.skill_id}
            label={skill?.skill_name}
          />
        ),
      )}
      {/* N-maxNumSkills link here */}
      {jobseekerID != null && leftoverSkillsCount > 0 ? (
        <Chip
          component={Link}
          clickable
          onClick={() => {}}
          key={"leftoverSkills"}
          label={"+" + leftoverSkillsCount}
          href={"/services/jobseekers/" + jobseekerID + "#skills"}
        />
      ) : (
        ""
      )}
    </Grid>
  );
}
