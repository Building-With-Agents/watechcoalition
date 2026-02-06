"use client";

import React, { useEffect, useState } from "react";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import PillButton from "@/app/ui/components/PillButton";
import TagsWithAutocomplete from "@/app/ui/components/mui/TagsWithAutocomplete";
import TextFieldWithSeparatedLabel from "@/app/ui/components/mui/TextFieldWithSeparatedLabel";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { JsShowcaseDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/lib/jobseekerStore";
import _ from "lodash";
import {
  initialState,
  setShowcase,
} from "@/lib/features/profileCreation/jobseekerSlice";
import {
  setPageDirty,
  setPageSaved,
} from "@/lib/features/profileCreation/saveSlice";
import { devLog } from "@/app/lib/utils";
import InputTextWithLabel from "@/app/ui/components/InputTextWithLabel";
import InputFileDropzone from "@/app/ui/components/InputFileDropzone";
import RequiredTooltip from "@/app/ui/components/mui/RequiredTooltip";
import { BlobPrefix } from "@/app/lib/services/azureBlobService";

export default function CreateJobseekerProfileShowcasePage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const dispatch = useDispatch();
  const showcaseStoreData = useSelector(
    (state: RootState) => state.jobseeker.showcase,
  );
  const showcaseData = { ...showcaseStoreData };

  const [hasUnmetRequired, setHasUnmetRequired] = useState("");

  const [introduction, setIntroduction] = useState(
    showcaseData.introduction ?? "",
  );
  const [resumeUrl, setResumeUrl] = useState<string | null>(
    showcaseData.resumeUrl,
  );

  const [skills, setSkills] = useState<SkillDTO[]>(showcaseData.skills);
  const [portfolioUrl, setPortfolioUrl] = useState(
    showcaseData.portfolioUrl ?? "",
  );
  const [portfolioPassword, setPortfolioPassword] = useState(
    showcaseData.portfolioPassword ?? "",
  );
  const [videoUrl, setVideoUrl] = useState(showcaseData.video_url ?? "");
  const [linkedInUrl, setLinkedInUrl] = useState(
    showcaseData.linkedin_url ?? "",
  );

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(showcaseStoreData, initialState.showcase)) {
          const { id } = session.user;

          try {
            console.log("fetching fresh");
            const response = await fetch(
              "/api/jobseekers/account/showcase/get/" + id,
            );

            if (!response.ok) {
              showcaseData.userId = id!;
            } else {
              const fetchedData: JsShowcaseDTO = (await response.json()).result;
              showcaseData.userId = id!;
              if (fetchedData.skills.length !== 0) {
                showcaseData.skills = fetchedData.skills;
                setSkills(showcaseData.skills);
              }
              if (fetchedData.introduction) {
                showcaseData.introduction = fetchedData.introduction;
                setIntroduction(showcaseData.introduction);
              }

              if (fetchedData.portfolioUrl) {
                showcaseData.portfolioUrl = fetchedData.portfolioUrl;
                setPortfolioUrl(showcaseData.portfolioUrl);
              }
              if (fetchedData.portfolioPassword) {
                showcaseData.portfolioPassword = fetchedData.portfolioPassword;
                setPortfolioPassword(showcaseData.portfolioPassword);
              }
              if (fetchedData.video_url) {
                showcaseData.video_url = fetchedData.video_url;
                setVideoUrl(showcaseData.video_url);
              }
              if (fetchedData.linkedin_url) {
                showcaseData.linkedin_url = fetchedData.linkedin_url;
                setLinkedInUrl(showcaseData.linkedin_url);
              }
            }

            const fetchedResumeData = await fetch(
              "/api/jobseekers/resume/get/" + id,
            );
            const fetchedResumeURL = await fetchedResumeData.json();

            if (response.ok) {
              if (typeof fetchedResumeURL === "string") {
                setResumeUrl(fetchedResumeURL);
              }
            }
          } catch (error) {
            console.error(error);
          }
        } else {
          console.log("fetching from store");
        }
      };
      dispatch(setPageSaved("showcase"));
      initializeFormFields();
    }
  }, [session?.user?.id]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }

    setHasUnmetRequired("");

    if (skills.length === 0) {
      setHasUnmetRequired("showcase-skills");
      return;
    }

    if (!Boolean(resumeUrl)) {
      setHasUnmetRequired("showcase-resume");
      return;
    }

    if (!validYouTubeLink(videoUrl)) {
      //TODO replace with stylized toast message
      alert("Please provide a valid YouTube URL before submitting.");
      return;
    }
    showcaseData.userId = session.user.id;
    showcaseData.skills = skills;
    showcaseData.portfolioUrl = portfolioUrl;
    showcaseData.portfolioPassword = portfolioPassword;
    showcaseData.video_url = videoUrl;
    showcaseData.linkedin_url = linkedInUrl;
    showcaseData.introduction = introduction;
    showcaseData.resumeUrl = resumeUrl;

    try {
      const response = await fetch("/api/jobseekers/account/showcase/upsert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(showcaseData),
      });

      if (response.ok) {
        const result = await response.json();
        devLog(JSON.stringify(result, null, 2));

        dispatch(setPageSaved("showcase"));
        dispatch(setShowcase(showcaseData));

        router.push("/edit-profile/jobseeker/education");
      } else {
        console.log(
          `Failed to submit showcase info. Status: ${response.status} - ${response.statusText}`,
        );
      }
    } catch (e: any) {
      console.log(`An unexpected error occurred: ${e.message}`);
    }
  }

  const handleResumeUpload = (url: string) => {
    // Update the local state with the uploaded image URL
    dispatch(setPageDirty("showcase"));
    setResumeUrl(url);
  };

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(3 / 6) * 100} />
        <p>Step 3/6</p>
        <h1>Showcase</h1>
        <p className="subtitle">* Indicates a required field</p>
        <form onSubmit={handleSubmit}>
          <fieldset>
            <legend>
              <h2>Introduce Yourself</h2>
              <p>
                This text will appear under your name in job candidate search
                listings and on your profile page.
              </p>
            </legend>

            <div className="profile-form-grid">
              <InputTextWithLabel
                id="profile-creation-intro-headlines"
                onChange={(e) => {
                  setIntroduction(e.target.value);
                }}
                placeholder="Example: I am a software engineer ..."
                value={introduction}
              >
                Introduction
              </InputTextWithLabel>
              {/*<InputTextWithLabel*/}
              {/*  id="profile-creation-intro-current-position"*/}
              {/*  onChange = {(e) => {*/}
              {/*    setCurrentJobTitle(e.target.value);*/}
              {/*  }}*/}
              {/*  placeholder="e.g., Software Developer"*/}
              {/*  value={*/}
              {/*    currentJobTitle*/}
              {/*  }*/}
              {/*>*/}
              {/*  Current Position*/}
              {/*</InputTextWithLabel>*/}
            </div>
          </fieldset>
          <fieldset>
            <legend>
              <h2>Skills</h2>
            </legend>
            <div className="profile-form-grid">
              <RequiredTooltip
                open={
                  hasUnmetRequired === "showcase-skills" && skills.length === 0
                }
                errorMessage="At least one skill is required"
              >
                <TagsWithAutocomplete
                  apiSearchRoute="/api/skills/search/"
                  fieldLabel="Select your top skills: *"
                  id="profile-creation-showcase-skills"
                  searchingText="Searching..."
                  noResultsText="No skills found..."
                  onChange={function (ev, val) {
                    if (val.every((skill) => typeof skill !== "string")) {
                      setSkills(val as SkillDTO[]);
                    }
                  }}
                  searchPlaceholder="Example: Java"
                  value={skills}
                  getTagLabel={(option: SkillDTO) => option.skill_name}
                  getTagLink={(option: SkillDTO) => option.skill_info_url}
                />
              </RequiredTooltip>

              <TextFieldWithSeparatedLabel
                id="profile-creation-showcase-portfolio"
                label="Portfolio"
                placeholder="Example: https://my.portfolio.website/"
                fullWidth
                value={portfolioUrl}
                onChange={(e) => {
                  setPortfolioUrl(e.target.value);
                }}
              />
              <TextFieldWithSeparatedLabel
                id="profile-creation-showcase-password"
                label="Portfolio Password (if applicable):"
                placeholder="Password"
                type="password"
                fullWidth
                value={portfolioPassword}
                onChange={(e) => {
                  setPortfolioPassword(e.target.value);
                }}
              />

              <TextFieldWithSeparatedLabel
                id="profile-creation-showcase-linkedin"
                label="LinkedIn URL:"
                placeholder="Example: https://www.linkedin.com/in/username"
                fullWidth
                value={linkedInUrl}
                error={!validLinkedInLink(linkedInUrl)}
                helperText={
                  !validLinkedInLink(linkedInUrl)
                    ? "Please enter a valid LinkedIn profile URL."
                    : ""
                }
                onChange={(e) => {
                  setLinkedInUrl(e.target.value);
                }}
              />
            </div>
          </fieldset>
          <fieldset>
            <div className="profile-form-grid">
              <legend>
                <h2>Video</h2>
              </legend>
              <p>
                In today&apos;s competitive job market, finding creative ways to
                elevate your profile is key. A personalized video introduction
                offers a unique opportunity to showcase your skills,
                personality, and career goals.
              </p>
              <ul className="list-inside list-disc">
                <li>
                  <b>Highlight Your Unique Value Proposition:</b> Share your
                  professional journey, key accomplishments, and why you are a
                  valuable asset to any team.
                </li>
                <li>
                  <b>Showcase Your Skills and Expertise:</b> Demonstrate your
                  technical skills, soft competencies, and how they can benefit
                  your future employers.
                </li>
                <li>
                  <b>Express Your Career Aspirations:</b> Articulate your
                  long-term career goals and how you see yourself growing
                  professionally.
                </li>
              </ul>
              {/*
            TODO: If we change our minds and want to implement video uploads, the button needs upload function added
            <Button pill className="custom-outline-btn">
              <MdOutlineFileUpload className="mr-2 h-5 w-5"/>
              Upload your video
            </Button>

            <DividerWithText>or</DividerWithText>
            */}
              Upload your YouTube video URL below and elevate your profile.
              <TextFieldWithSeparatedLabel
                id="profile-creation-showcase-video"
                label="Video URL:"
                placeholder="Example: https://www.youtube.com/watch"
                fullWidth
                value={videoUrl}
                error={!validYouTubeLink(videoUrl)}
                onChange={(e) => {
                  setVideoUrl(e.target.value);
                }}
              />
            </div>
          </fieldset>
          <div>
            Resume:
            <InputFileDropzone
              id="profile-creation-intro-resume"
              fileTypeText="PDF"
              blobPrefix={"resume" as BlobPrefix}
              accept=".pdf"
              maxSizeMB={5}
              userId={session?.user?.id!}
              onDocUpload={handleResumeUpload}
              autoloadedUrl={
                resumeUrl !== "" ? (resumeUrl ?? undefined) : undefined
              }
            />
          </div>
          <div className="profile-form-progress-btn-group">
            <PillButton
              variant="outlined"
              onClick={() => {
                router.push("/edit-profile/jobseeker/preferences");
              }}
            >
              Previous
            </PillButton>
            <PillButton type="submit">Save and continue</PillButton>
          </div>
        </form>
      </section>
    </main>
  );
}

function validYouTubeLink(url: string) {
  if (url == "") return true;
  const regex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$/;
  return regex.test(url);
}

function validLinkedInLink(url: string) {
  if (url == "") return true;
  const regex =
    /^(https?:\/\/)?(www\.)?(linkedin\.com)\/in\/[A-Za-z0-9_-]{3,100}\/?.*$/i;
  return regex.test(url);
}
