"use client";
import Avatar from "../Avatar";
import { useSession } from "next-auth/react";
import { Role } from "@/data/dtos/UserInfoDTO";
import Bookmark from "../Bookmark";
import PillButton from "@/app/ui/components/PillButton";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { JobListingCardViewDTO } from "@/data/dtos/JobListingCardViewDTO";
import { Alert, Card, Chip, Grid, Stack, Typography } from "@mui/material";
import { Circle } from "@mui/icons-material";
import Link from "next/link";
import React, { useMemo } from "react";

function extractTextFromHTML(htmlString: string) {
  const tempElement = document.createElement("div");
  tempElement.innerHTML = htmlString;
  // Add spaces between block-level elements
  const blockElements = tempElement.querySelectorAll(
    "p, div, h1, h2, h3, h4, h5, h6, li",
  );
  blockElements.forEach((element) => {
    element.insertAdjacentText("afterend", " ");
  });
  // Get the text content and normalize spaces
  let text = tempElement.textContent || tempElement.innerText || "";
  // Replace multiple spaces, newlines, and tabs with a single space
  text = text.replace(/\s+/g, " ").trim();

  return text;
}

function JobListingCardView({
  joblisting,
}: {
  joblisting: JobListingCardViewDTO;
}) {
  const { data: session } = useSession();

  const job_title: string = joblisting?.job_title;
  const company_name: string = joblisting.companies.company_name;
  const company_image: string | undefined =
    joblisting.companies.company_logo_url ?? undefined;
  const skills: SkillDTO[] = joblisting.skills ?? [];
  const salary_range: string = joblisting?.salary_range ?? "";
  const description: string = useMemo(
    () => extractTextFromHTML(joblisting?.job_description ?? ""),
    [joblisting?.job_description],
  );
  const isBookmarked = joblisting?.isBookmarked ?? false;
  const isJobseeker = session?.user.roles.includes(Role.JOBSEEKER);

  return (
    <Card
      elevation={0}
      sx={{
        p: { xs: 0.5, sm: 1, md: 3 },
        borderRadius: "12px",
        transition: "box-shadow 0.3s",

        "&:hover": { boxShadow: 3 },
      }}
    >
      {joblisting.career_services_offered && (
        <Grid container sx={{ mb: 3 }}>
          <Alert color="info">Employer Partner Job</Alert>
        </Grid>
      )}
      <Stack
        direction={"row"}
        sx={{ alignItems: "center", justifyContent: "space-between" }}
      >
        <Stack direction={"row"} spacing={2} sx={{ alignItems: "center" }}>
          {company_image && (
            <div className="shrink-0">{<Avatar imgsrc={company_image} />}</div>
          )}
          <Typography
            sx={{ color: "neutral.900", opacity: 0.6, fontWeight: 500 }}
          >
            {company_name}
          </Typography>
        </Stack>
        {isJobseeker ? (
          <Bookmark
            bookmarked={isBookmarked}
            addUrl={
              "/api/joblistings/bookmark/add/" + joblisting.job_posting_id
            }
            removeUrl={
              "/api/joblistings/bookmark/remove/" + joblisting.job_posting_id
            }
          />
        ) : (
          ""
        )}
      </Stack>
      <Typography variant="h5" sx={{ my: 1, textTransform: "capitalize" }}>
        {job_title}
      </Typography>
      <Grid
        container
        columnSpacing={2}
        sx={{ alignItems: "center", textTransform: "capitalize" }}
      >
        <Typography>{joblisting?.location}</Typography>
        <Circle sx={{ fontSize: 8 }} />
        <Typography>
          {joblisting?.employment_type === "Earn and Learn"
            ? joblisting?.earn_and_learn_type
            : joblisting?.employment_type}
        </Typography>
        <Circle sx={{ fontSize: 8 }} />
        <Typography>
          {joblisting?.company_addresses?.locationData.city}
        </Typography>
        <Circle sx={{ fontSize: 8 }} />
        <Typography>{joblisting?.is_paid ? salary_range : "unpaid"}</Typography>
        <Circle sx={{ fontSize: 8 }} />
        <Typography>
          Deadline:{" "}
          {joblisting?.unpublish_date
            ? new Date(joblisting.unpublish_date).toLocaleDateString("en-us", {
                month: "numeric",
                day: "numeric",
                year: "numeric",
              })
            : "N/A"}
        </Typography>
      </Grid>
      <Typography
        component={"div"}
        sx={{
          mt: 1,
          display: "-webkit-box",
          WebkitLineClamp: 2,
          WebkitBoxOrient: "vertical",
          overflowWrap: "break-word",
          overflow: "hidden",
        }}
      >
        {description}
      </Typography>

      {skills.length > 0 && (
        <Grid container gap={1} sx={{ mt: 1 }}>
          {skills.map((skill) =>
            skill?.skill_info_url.length > 0 ? (
              <Chip
                component={Link}
                clickable
                onClick={() => {}}
                key={skill?.skill_id}
                label={skill?.skill_name}
                target="_blank"
                href={skill?.skill_info_url}
              />
            ) : (
              <Chip
                clickable={false}
                onClick={() => {}}
                key={skill?.skill_id}
                label={skill?.skill_name}
              />
            ),
          )}
        </Grid>
      )}
      <Stack
        direction={{ xs: "column", sm: "row" }}
        sx={{ mt: 2, justifyContent: "flex-end" }}
      >
        <PillButton
          href={`/services/joblistings/${joblisting.job_posting_id}`}
          target="_blank"
          variant="outlined"
          color="secondary"
        >
          View job posting
        </PillButton>
      </Stack>
    </Card>
  );
}

export default React.memo(JobListingCardView);
