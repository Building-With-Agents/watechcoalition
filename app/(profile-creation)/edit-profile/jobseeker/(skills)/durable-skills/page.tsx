"use client";
import {
  DurableSkillsRatings,
  SkillLevel,
  SkillLevelLabels,
} from "@/app/lib/admin/careerPrep";
import { devLog } from "@/app/lib/utils";
import PillButton from "@/app/ui/components/PillButton";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import { JsCareerPrepDurableSkillsDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import {
  initialState,
  setDurableSkills,
} from "@/lib/features/profileCreation/jobseekerSlice";
import { RootState } from "@/lib/jobseekerStore";
import {
  Container,
  Radio,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import _ from "lodash";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

export default function Page() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const dispatch = useDispatch();
  const durableSkillsStoreData = useSelector(
    (state: RootState) => state.jobseeker.durableSkills,
  );
  const [localDurableSkills, setLocalDurableSkills] = useState(
    durableSkillsStoreData,
  );

  const proficiencyOptions = Object.entries(SkillLevel)
    .filter(([key]) => isNaN(Number(key)))
    .map(([label, value]) => ({ label, value }));

  const questions = [
    {
      id: "emotionManagement",
      text: "Understanding and managing my own emotions.",
    },
    {
      id: "empathy",
      text: "Empathizing with and understanding the emotions of others.",
    },
    {
      id: "goalSetting",
      text: "Setting and achieving goals effectively.",
    },
    {
      id: "timeManagement",
      text: "Managing my time efficiently and prioritizing tasks.",
    },
    {
      id: "adaptability",
      text: "Learning from my mistakes and adapting to new situations.",
    },
    {
      id: "criticalThinking",
      text: "Thinking critically and solving problems effectively.",
    },
    {
      id: "creativity",
      text: "Generating new and innovative ideas.",
    },
    {
      id: "resilience",
      text: "Persisting through challenges and setbacks.",
    },
    {
      id: "communication",
      text: "Communicating clearly and effectively, both verbally and in writing.",
    },
    {
      id: "activeListening",
      text: "Actively listening to others and understanding their perspectives.",
    },
    {
      id: "conflictResolution",
      text: "Resolving conflicts peacefully and constructively.",
    },
    {
      id: "nonverbalCommunication",
      text: "Using nonverbal communication effectively to convey my message.",
    },
    {
      id: "teamwork",
      text: "Working effectively as part of a team and collaborating with others.",
    },
    {
      id: "trustBuilding",
      text: "Building trust and rapport with others.",
    },
    {
      id: "leadership",
      text: "Taking on leadership roles when appropriate and following the lead of others when necessary.",
    },
    {
      id: "perspectiveTaking",
      text: "Understanding and appreciating the perspectives of others, even when they differ from my own.",
    },
    {
      id: "culturalAwareness",
      text: "Being aware of cultural differences and adapting my communication style accordingly.",
    },
    {
      id: "relationshipBuilding",
      text: "Building and maintaining strong relationships with others.",
    },
    {
      id: "documentationSkills",
      text: "Creating clear and meaningful documentation or presentations to clearly communicate an idea.",
    },
  ];

  const allQuestionsAnswered = questions.every((question) => {
    return (
      localDurableSkills.CareerPrepAssessment?.durableSkills &&
      typeof (localDurableSkills.CareerPrepAssessment.durableSkills as any)[
        question.id
      ] !== "undefined"
    );
  });

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(localDurableSkills, initialState.durableSkills)) {
          const { id } = session.user;

          try {
            const response = await fetch(
              "/api/jobseekers/account/durable-skills/get/" + id,
            );

            if (!response.ok) {
            } else {
              const fetchedData: JsCareerPrepDurableSkillsDTO = (
                await response.json()
              ).result;
              setLocalDurableSkills(fetchedData);
              devLog(fetchedData);
            }
          } catch (error) {
            console.error(error);
          }
        } else {
          devLog("fetching from store");
        }
      };
      initializeFormFields();
    }
  }, [session?.user?.id, status]);

  function handleRadioChange(
    questionId: keyof DurableSkillsRatings,
    value: SkillLevel,
  ) {
    setLocalDurableSkills((prev) => ({
      ...prev,
      CareerPrepAssessment: {
        durableSkills: {
          ...(prev.CareerPrepAssessment.durableSkills as any),
          [questionId]: value,
        },
      },
    }));
    devLog(questionId, value);
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }
    try {
      const response = await fetch(
        "/api/jobseekers/account/durable-skills/upsert",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(localDurableSkills),
        },
      );

      if (response.ok) {
        dispatch(setDurableSkills(localDurableSkills));
        router.push("/edit-profile/jobseeker/professional-branding");
      }
    } catch {}
  }

  return (
    <Container maxWidth="md">
      <ProgressBarFlat progress={(7 / 9) * 100} />
      <Typography sx={{ mb: 1 }}>Step 7/9</Typography>
      <Typography variant="h3" sx={{ fontWeight: 700 }}>
        Durable Skills Assessment
      </Typography>
      <Typography sx={{ my: 2 }}>
        Soft skills are undergoing a rebranding, and in lieu of the word soft,
        many people are now referring to them as durable. But that&apos;s not
        all—there has been a considerable shift in the demand of durable skills
        as more employers see their increase in value, and more hiring managers
        switch to a skills-based hiring model.
      </Typography>
      <Typography color="secondary">
        Remember: Your responses will help us understand your current skills and
        identify areas where you might need support in reaching your career
        goals.
      </Typography>
      <form onSubmit={handleSubmit}>
        <Table stickyHeader sx={{ mt: 2, mb: 5 }}>
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              {proficiencyOptions.map((option) => (
                <TableCell key={option.value}>
                  {SkillLevelLabels[option.value as SkillLevel]}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {questions.map((question) => (
              <TableRow key={question.id}>
                <TableCell>{question.text}</TableCell>
                {proficiencyOptions.map((option) => (
                  <TableCell key={option.value}>
                    <Radio
                      name={question.id.toString()}
                      value={option.value}
                      checked={
                        localDurableSkills.CareerPrepAssessment?.durableSkills
                          ? (
                              localDurableSkills.CareerPrepAssessment
                                .durableSkills as any
                            )[question.id] === option.value
                          : false
                      }
                      onChange={() =>
                        handleRadioChange(
                          question.id as keyof DurableSkillsRatings,
                          option.value as SkillLevel,
                        )
                      }
                    />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <Stack direction="row" sx={{ justifyContent: "space-between", mb: 5 }}>
          <PillButton
            variant="outlined"
            onClick={() => {
              router.push("/edit-profile/jobseeker/technical-skills");
            }}
          >
            Previous
          </PillButton>
          <PillButton disabled={!allQuestionsAnswered} type="submit">
            Save and Continue
          </PillButton>
        </Stack>
      </form>
    </Container>
  );
}
