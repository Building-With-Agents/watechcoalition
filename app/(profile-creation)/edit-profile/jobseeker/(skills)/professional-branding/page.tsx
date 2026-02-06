"use client";
import {
  ProfessionalBrandingRatings,
  AgreementLevel,
  AgreementLevelLabels,
} from "@/app/lib/admin/careerPrep";
import { devLog } from "@/app/lib/utils";
import PillButton from "@/app/ui/components/PillButton";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import { JsCareerPrepProfessionalBrandingDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import {
  initialState,
  setProfessionalBranding,
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
  const professionalBrandingSkillsStoreData = useSelector(
    (state: RootState) => state.jobseeker.professionalBranding,
  );
  const [localProfesionalBranding, setLocalProfesionalBranding] = useState(
    professionalBrandingSkillsStoreData,
  );

  const proficiencyOptions = Object.entries(AgreementLevel)
    .filter(([key]) => isNaN(Number(key)))
    .map(([label, value]) => ({ label, value }));

  const questions = [
    {
      id: "personalBrand",
      text: "I have a clear and consistent personal brand that reflects my skills, values, and career goals.",
    },
    {
      id: "onlinePresence",
      text: "I manage my online presence effectively, including my social media an networking profiles.",
    },
    {
      id: "elevatorPitch",
      text: "I can deliver a concise and compelling elevator pitch that highlights my skills and career goals.",
    },
    {
      id: "resumeEffectiveness",
      text: "I have a resume that effectively showcases my skills, experiences, and achievements.",
    },
    {
      id: "coverLetterEffectiveness",
      text: "I have a cover letter template and am successful at tailoring it to each job application to highlight my relevant qualifications.",
    },
    {
      id: "interviewExperience",
      text: "I have experience with different types of interviews, including technical, behavioral, virtual, and in-person interviews.",
    },
    {
      id: "responseTechnique",
      text: "I am familiar with and confident in my ability to use effective response techniques to answer interview questions.",
    },
    {
      id: "followUpImportance",
      text: "I understand the importance of following up after an interview and can effectively do so.",
    },
    {
      id: "onlineNetworking",
      text: "I am familiar with best practices for using online platforms to connect with potential employers and industry professionals.",
    },
    {
      id: "eventNetworking",
      text: "I am confident attending industry events and career fairs to expand my professional network.",
    },
    {
      id: "relationshipManagement",
      text: "I can successfully maintain and nurture professional relationships over time.",
    },
    {
      id: "jobSearchStrategy",
      text: "I am able to effectively search for job opportunities and tailor my job search strategy to my career goals.",
    },
    {
      id: "materialDistribution",
      text: "I am familiar with best practices for distributing professional materials to potential employers.",
    },
    {
      id: "networkingTechniques",
      text: "I am able to use effective networking techniques, such as informational interviewing and active listening. ",
    },
    {
      id: "onboardingBestPractices",
      text: "I am familiar with best practices for onboarding and can effectively adapt to a new role.",
    },
    {
      id: "developmentPlan",
      text: "I have experience with creating and implementing a personal development plan in a new role to enhance my skills and career prospects.",
    },
    {
      id: "mentorship",
      text: "I can confidently seek mentorship and coaching within my networks to support my career development.",
    },
  ];

  const allQuestionsAnswered = questions.every((question) => {
    return (
      localProfesionalBranding.CareerPrepAssessment
        ?.professionalBrandingAndJobMarketReadiness &&
      typeof (
        localProfesionalBranding.CareerPrepAssessment
          .professionalBrandingAndJobMarketReadiness as any
      )[question.id] !== "undefined"
    );
  });

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (
          _.isEqual(localProfesionalBranding, initialState.professionalBranding)
        ) {
          const { id } = session.user;

          try {
            const response = await fetch(
              "/api/jobseekers/account/professional-branding/get/" + id,
            );

            if (!response.ok) {
            } else {
              const fetchedData: JsCareerPrepProfessionalBrandingDTO = (
                await response.json()
              ).result;
              setLocalProfesionalBranding(fetchedData);
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
    questionId: keyof ProfessionalBrandingRatings,
    value: AgreementLevel,
  ) {
    setLocalProfesionalBranding((prev) => ({
      ...prev,
      CareerPrepAssessment: {
        professionalBrandingAndJobMarketReadiness: {
          ...(prev.CareerPrepAssessment
            .professionalBrandingAndJobMarketReadiness as any),
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
        "/api/jobseekers/account/professional-branding/upsert",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(localProfesionalBranding),
        },
      );

      if (response.ok) {
        dispatch(setProfessionalBranding(localProfesionalBranding));
        router.push("/edit-profile/jobseeker/disclosures");
      }
    } catch {}
  }

  return (
    <Container maxWidth="md">
      <ProgressBarFlat progress={(8 / 9) * 100} />
      <Typography sx={{ mb: 1 }}>Step 8/9</Typography>
      <Typography variant="h3" sx={{ fontWeight: 700 }}>
        Professional Branding & Job Market Readiness
      </Typography>
      <Typography color="secondary" sx={{ my: 2 }}>
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
                  {AgreementLevelLabels[option.value as AgreementLevel]}
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
                        localProfesionalBranding.CareerPrepAssessment
                          ?.professionalBrandingAndJobMarketReadiness
                          ? (
                              localProfesionalBranding.CareerPrepAssessment
                                .professionalBrandingAndJobMarketReadiness as any
                            )[question.id] === option.value
                          : false
                      }
                      onChange={() =>
                        handleRadioChange(
                          question.id as keyof ProfessionalBrandingRatings,
                          option.value as AgreementLevel,
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
              router.push("/edit-profile/jobseeker/durable-skills");
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
