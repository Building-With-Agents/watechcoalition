"use client";

import React, { useEffect, useState } from "react";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import SelectWithLabel from "@/app/ui/components/mui/SelectWithLabel";
import { JsDisclosuresDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { useRouter } from "next/navigation";
import PillButton from "@/app/ui/components/PillButton";

import {
  Box,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  FormLabel,
  Link,
  Radio,
  RadioGroup,
} from "@mui/material";
import { useSession } from "next-auth/react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/lib/jobseekerStore";
import {
  initialState,
  setDisclosures,
} from "@/lib/features/profileCreation/jobseekerSlice";
import {
  setPageDirty,
  setPageSaved,
} from "@/lib/features/profileCreation/saveSlice";
import _ from "lodash";
import { devLog } from "@/app/lib/utils";
import { PriorityPopulationList } from "@/app/lib/admin/eduProviderPartner";

export default function CreateJobseekerProfileDisclosuresPage() {
  const router = useRouter();
  const dispatch = useDispatch();
  const { data: session, status } = useSession();
  const disclosuresStoreData = useSelector(
    (state: RootState) => state.jobseeker.disclosures,
  );
  const disclosuresData = { ...disclosuresStoreData };
  const [error, setError] = useState<{ error: string | null }>({ error: null }); // eslint-disable-line @typescript-eslint/no-unused-vars

  const [veteranStatus, setVeteranStatus] = useState(disclosuresData.isVeteran);
  const [disabilityStatus, setDisabilityStatus] = useState(
    disclosuresData.disabilityStatus,
  );
  const [disabilityType, setDisabilityType] = useState(
    disclosuresData.disability,
  );
  const [gender, setGender] = useState(disclosuresData.gender);
  const [race, setRace] = useState(disclosuresData.race);
  const [ethnicity, setEthnicity] = useState(disclosuresData.ethnicity);
  const [priorityPopulations, setPriorityPopulations] = useState<
    PriorityPopulationList[] | undefined
  >(
    (disclosuresData.CareerPrepAssessment.priorityPopulations?.split(
      "~",
    ) as PriorityPopulationList[]) ?? [],
  );

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(disclosuresStoreData, initialState.disclosures)) {
          const { id } = session.user;

          try {
            devLog("fetching fresh");
            const response = await fetch(
              "/api/jobseekers/account/disclosures/get/" + id,
            );

            if (!response.ok) {
              disclosuresData.userId = id!;
            } else {
              const fetchedData: JsDisclosuresDTO = (await response.json())
                .result;
              disclosuresData.userId = id!;
              if (fetchedData.gender) {
                disclosuresData.gender = fetchedData.gender;
                setGender(disclosuresData.gender);
              }
              if (fetchedData.disabilityStatus) {
                disclosuresData.disabilityStatus = fetchedData.disabilityStatus;
                setDisabilityStatus(disclosuresData.disabilityStatus);
              }
              if (fetchedData.disability) {
                disclosuresData.disability = fetchedData.disability;
                setDisabilityType(disclosuresData.disability);
              }
              if (fetchedData.isVeteran) {
                disclosuresData.isVeteran = fetchedData.isVeteran;
                setVeteranStatus(disclosuresData.isVeteran);
              }
              if (fetchedData.ethnicity) {
                disclosuresData.ethnicity = fetchedData.ethnicity;
                setEthnicity(disclosuresData.ethnicity);
              }
              if (fetchedData.race) {
                disclosuresData.race = fetchedData.race;
                setRace(disclosuresData.race);
              }
              if (!disclosuresData.CareerPrepAssessment) {
                disclosuresData.CareerPrepAssessment = {};
              } else {
                disclosuresData.CareerPrepAssessment = {
                  ...disclosuresData.CareerPrepAssessment,
                };
                if (fetchedData.CareerPrepAssessment.priorityPopulations) {
                  disclosuresData.CareerPrepAssessment.priorityPopulations =
                    fetchedData.CareerPrepAssessment.priorityPopulations;
                  setPriorityPopulations(
                    fetchedData.CareerPrepAssessment.priorityPopulations.split(
                      "~",
                    ) as PriorityPopulationList[],
                  );
                }
              }
            }
          } catch (error) {
            console.error(error);
          }
        } else {
          devLog("fetching from store");
          devLog(disclosuresStoreData);
        }
      };

      dispatch(setPageSaved("disclosures"));
      initializeFormFields();
    }
  }, [session?.user?.id]);

  const handlePrioritySelect = (type: PriorityPopulationList): void => {
    console.log(priorityPopulations);
    setPriorityPopulations((prev) => {
      const currentSelections = prev ?? [];
      if (currentSelections.includes(type)) {
        return currentSelections.filter((t) => t !== type);
      } else {
        return [...currentSelections, type];
      }
    });
  };

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }

    const updatedDisclosures = {
      ...disclosuresData,
      userId: session.user.id,
      isVeteran: veteranStatus,
      disabilityStatus: disabilityStatus,
      disability: disabilityType,
      gender: gender,
      race: race,
      ethnicity: ethnicity,
      CareerPrepAssessment: {
        ...(disclosuresData.CareerPrepAssessment || {}), // Start with existing properties
        priorityPopulations: priorityPopulations
          ? priorityPopulations.join("~")
          : undefined,
      },
    };

    try {
      const response = await fetch(
        "/api/jobseekers/account/disclosures/upsert",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(updatedDisclosures),
        },
      );
      if (response.ok) {
        dispatch(setPageSaved("disclosures"));
        dispatch(setDisclosures(updatedDisclosures));
      } else {
        const errorMessage = `Failed to submit disclosure info. Status: ${response.status} - ${response.statusText}`;
        setError({ error: errorMessage });
      }
      router.push("/edit-profile/jobseeker/congratulations");
    } catch (e: any) {
      setError({ error: `An unexpected error occurred: ${e.message}` });
    }
  }

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(6 / 6) * 100} />
        <p>Step 6/6</p>

        <h1>Voluntary Disclosures</h1>
        <p className="subtitle">* Indicates a required field</p>
        <p>* Indicates a required field</p>
        <form onSubmit={handleSubmit}>
          <p>
            You are invited to provide information to assist us in meeting these
            government reporting requirements. Completion of this form is
            completely voluntary. If you choose not to answer, you will not be
            subject to adverse effects. However, we encourage you to answer each
            question and assure you that this information is confidential.
          </p>
          <Box sx={{ my: 1 }}>
            <p>For information about the WJI and GJC Grant, visit:</p>
            <Link
              target="_blank"
              href="https://wsac.wa.gov/sites/default/files/Washington-Student-Achievement-Project-Narrative.pdf"
            >
              https://wsac.wa.gov/sites/default/files/Washington-Student-Achievement-Project-Narrative.pdf
            </Link>
          </Box>
          <fieldset>
            <div className="profile-form-grid">
              <SelectWithLabel
                id="profile-creation-disclosures-gender"
                fullWidth
                label="Gender *"
                value={gender}
                onChange={(event) => {
                  dispatch(setPageDirty("disclosures"));
                  setGender(event.target.value);
                }}
                options={[
                  { label: "Male", value: "male" },
                  { label: "Female", value: "female" },
                  {
                    label: "Do not identify as male or female",
                    value: "Do not identify as male or female",
                  },
                  { label: "I prefer not to say", value: "undisclosed" },
                ]}
                placeholder="Please select"
                required
              />
              <SelectWithLabel
                id="profile-creation-disclosures-veterans"
                fullWidth
                label="Veterans *"
                value={veteranStatus}
                onChange={(event) => {
                  dispatch(setPageDirty("disclosures"));
                  setVeteranStatus(event.target.value);
                }}
                options={[
                  { label: "Yes", value: "yes" },
                  { label: "No", value: "no" },
                  { label: "I prefer not to say", value: "undisclosed" },
                ]}
                placeholder="Please select"
                required
              />
              <SelectWithLabel
                id="profile-creation-disclosures-ethnicity"
                fullWidth
                label="Ethnicity *"
                value={ethnicity}
                onChange={(event) => {
                  dispatch(setPageDirty("disclosures"));
                  setEthnicity(event.target.value);
                }}
                options={[
                  {
                    label: "I am a person of Hispanic origin",
                    value: "hispanic origin",
                  },
                  { label: "I am NOT Hispanic", value: "not hispanic" },
                  { label: "I prefer not to say", value: "undisclosed" },
                ]}
                placeholder="Please select"
                required
              />
              <SelectWithLabel
                id="profile-creation-disclosures-race"
                fullWidth
                label="Race *"
                value={race}
                onChange={(event) => {
                  dispatch(setPageDirty("disclosures"));
                  setRace(event.target.value);
                }}
                options={[
                  { label: "Asian", value: "Asian" },
                  {
                    label: "Black or African American",
                    value: "Black or African American",
                  },
                  { label: "White / Caucasian", value: "White / Caucasian" },
                  {
                    label: "Native Hawaiian or Pacific Islander",
                    value: "Native Hawaiian or Pacific Islander",
                  },
                  { label: "Hispanic", value: "Hispanic" },
                  {
                    label: "American Indian or Alaska Native",
                    value: "American Indian or Alaska Native",
                  },
                  { label: "Multi-race", value: "Multi-race" },
                  {
                    label: "Not Elsewhere Classified / Other",
                    value: "Not Elsewhere Classified / Other",
                  },
                  {
                    label: "Not Specified / Unknown",
                    value: "Not Specified / Unknown",
                  },
                ]}
                placeholder="Please select"
                required
              />
            </div>
          </fieldset>
          <fieldset>
            <FormControl component="fieldset">
              <FormLabel component="legend">
                Please indicate if you identify with any of the following
                priority populations:
              </FormLabel>
              <FormHelperText sx={{ m: 0 }}>
                Select all that apply
              </FormHelperText>
              <FormGroup>
                {Object.values(PriorityPopulationList).map((type) => (
                  <FormControlLabel
                    key={type}
                    control={
                      <Checkbox
                        checked={priorityPopulations?.includes(type)}
                        onChange={() => handlePrioritySelect(type)}
                      />
                    }
                    label={type}
                  />
                ))}
              </FormGroup>
            </FormControl>
          </fieldset>
          <fieldset>
            <legend>
              <h2>How do you know if you have a disability?</h2>
            </legend>
            <p>
              A disability is a condition that substantially limits one or more
              of your “major life activities.” If you have or have ever had such
              a condition, you are a person with a disability. Disabilities
              include, but are not limited to:
            </p>

            <ul
              className="list-inside list-disc"
              style={{
                paddingBottom: "1em",
                paddingLeft: "1em",
              }}
            >
              <li>
                Alcohol or other substance use disorder (not currently using
                drugs illegally)
              </li>
              <li>
                Autoimmune disorder, for example, lupus, fibromyalgia,
                rheumatoid arthritis, HIV/AIDS
              </li>
              <li>Blind or low vision</li>
              <li>Cancer (past or present)</li>
              <li>Cardiovascular or heart disease</li>
              <li>Celiac disease</li>
              <li>Cerebral palsy</li>
              <li>Deaf or serious difficulty hearing</li>
              <li>Diabetes</li>
              <li>
                Disfigurement, for example, disfigurement caused by burns,
                wounds, accidents, or congenital disorders
              </li>
              <li>Epilepsy or other seizure disorder</li>
              <li>
                Gastrointestinal disorders, for example, Crohn&apos;s Disease,
                irritable bowel syndrome
              </li>
              <li>Intellectual or developmental disability</li>
              <li>
                Mental health conditions, for example, depression, bipolar
                disorder, anxiety disorder, schizophrenia, PTSD
              </li>
              <li>Missing limbs or partially missing limbs</li>
              <li>
                Mobility impairment, benefiting from the use of a wheelchair,
                scooter, walker, leg brace(s) and/or other supports
              </li>
              <li>
                Nervous system condition, for example, migraine headaches,
                Parkinson&apos;s disease, multiple sclerosis (MS)
              </li>
              <li>
                Neurodivergence, for example, attention-deficit/hyperactivity
                disorder (ADHD), autism spectrum disorder, dyslexia, dyspraxia,
                other learning disabilities
              </li>
              <li>Partial or complete paralysis (any cause)</li>
              <li>
                Pulmonary or respiratory conditions, for example, tuberculosis,
                asthma, emphysema
              </li>
              <li>Short stature (dwarfism)</li>
              <li>Traumatic brain injury</li>
            </ul>
            <FormControl component="fieldset">
              <FormLabel
                className="mb-2 mt-5"
                id="profile-creation-disclosures-require-disability-label"
                component="legend"
                sx={{ color: "#000000ff" }}
              >
                Please select one of the options below: *
              </FormLabel>
              <RadioGroup
                aria-labelledby="profile-creation-disclosures-require-disability-label"
                value={disabilityStatus}
                onChange={(event) => {
                  setDisabilityStatus(event.target.value);
                  if (event.target.value !== "yes") {
                    dispatch(setPageDirty("disclosures"));
                    setDisabilityType("");
                  }
                }}
                name="profile-creation-disclosures-require-disability"
              >
                <FormControlLabel
                  value="yes"
                  control={<Radio required />}
                  label="Yes, I have a disability, or have had one in the past"
                  sx={{
                    "& .MuiFormControlLabel-asterisk": {
                      display: "none",
                    },
                  }}
                />
                <FormControlLabel
                  value="none"
                  control={<Radio required />}
                  label="No, I do not have a disability and have not had one in the past"
                  sx={{
                    "& .MuiFormControlLabel-asterisk": {
                      display: "none",
                    },
                  }}
                />
                <FormControlLabel
                  value="undisclosed"
                  control={<Radio required />}
                  label="I do not want to answer"
                  sx={{
                    "& .MuiFormControlLabel-asterisk": {
                      display: "none",
                    },
                  }}
                />
              </RadioGroup>
            </FormControl>
            {disabilityStatus === "yes" && (
              <div className="mb-2 mt-5">
                <SelectWithLabel
                  id="profile-creation-disclosures-require-disability-label"
                  fullWidth
                  label="Please specify: *"
                  value={disabilityType}
                  onChange={(event) => {
                    dispatch(setPageDirty("disclosures"));
                    setDisabilityType(event.target.value);
                  }}
                  options={[
                    { label: "I prefer not to say", value: "undisclosed" },
                    { label: "Cognitive", value: "cognitive" },
                    { label: "Emotional", value: "emotional" },
                    { label: "Hearing", value: "hearing" },
                    { label: "Mental", value: "mental" },
                    { label: "Physical", value: "physical" },
                    { label: "Visual", value: "visual" },
                    { label: "Other", value: "other" },
                  ]}
                  placeholder="Please select"
                  required
                />
              </div>
            )}
          </fieldset>
          <div className="profile-form-progress-btn-group">
            <PillButton
              variant="outlined"
              onClick={() => {
                router.push("/edit-profile/jobseeker/professional-branding");
              }}
            >
              Previous
            </PillButton>
            <PillButton type="submit">Submit</PillButton>
          </div>
        </form>
      </section>
    </main>
  );
}
