"use client";

import React, { useEffect, useState } from "react";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import PillButton from "@/app/ui/components/PillButton";
import { useRouter } from "next/navigation";
import { JsPreferencesDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { useSession } from "next-auth/react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/lib/jobseekerStore";
import {
  initialState,
  setPreferences,
} from "@/lib/features/profileCreation/jobseekerSlice";
import { setPageSaved } from "@/lib/features/profileCreation/saveSlice";
import _ from "lodash";
import { devLog } from "@/app/lib/utils";
import {
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Radio,
  RadioGroup,
  Checkbox,
  Stack,
} from "@mui/material";
import { CareerPrepPathways } from "@/app/lib/admin/careerPrep";

export default function CreateJobseekerProfilePreferencesPage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const dispatch = useDispatch();
  const preferencesStoreData = useSelector(
    (state: RootState) => state.jobseeker.preferences,
  );
  const preferencesData = { ...preferencesStoreData };
  const [error, setError] = useState<string | null>(null);

  const EMPLOYMENT_OPTIONS = [
    "Full-time",
    "Part-time",
    "Internship",
    "On-campus",
  ] as const;
  type EmploymentLabel = (typeof EMPLOYMENT_OPTIONS)[number];

  const parseCSV = (s?: string | null): string[] =>
    (s ?? "")
      .split(",")
      .map((v) => v.trim())
      .filter(Boolean);

  const toCSV = (arr: string[]): string =>
    [...new Set(arr.map((v) => v.trim()))].join(",");

  const [employmentTypes, setEmploymentTypes] = useState<string[]>(
    parseCSV(preferencesData.preferredEmploymentType),
  );

  const [pathway, setPathway] = useState(preferencesData.targetedPathway ?? "");
  const [pathwayId, setPathwayId] = useState(
    preferencesData.targetedPathwayId ?? "",
  );

  const toggleEmployment = (label: EmploymentLabel, checked: boolean) => {
    setEmploymentTypes((prev) =>
      checked ? [...prev, label] : prev.filter((l) => l !== label),
    );
  };

  useEffect(() => {
    devLog("Selected employment types:", employmentTypes);
  }, [employmentTypes]);

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(preferencesStoreData, initialState.preferences)) {
          const { id } = session.user;

          try {
            devLog("fetching fresh");
            const response = await fetch(
              "/api/jobseekers/account/preferences/get/" + id,
            );

            if (!response.ok) {
              preferencesData.userId = id!;
            } else {
              const fetchedData: JsPreferencesDTO = (await response.json())
                .result;
              preferencesData.userId = id!;

              if (fetchedData.preferredEmploymentType) {
                const list = parseCSV(fetchedData.preferredEmploymentType);
                preferencesData.preferredEmploymentType = toCSV(list);
                setEmploymentTypes(list);
              }

              if (fetchedData.targetedPathway) {
                preferencesData.targetedPathway = fetchedData.targetedPathway;
                setPathway(preferencesData.targetedPathway);
              }
              if (fetchedData.targetedPathwayId) {
                preferencesData.targetedPathwayId =
                  fetchedData.targetedPathwayId;
                setPathwayId(preferencesData.targetedPathwayId);
              }
            }
          } catch (error) {
            console.error(error);
          }
        } else {
          devLog("fetching from store");
          setEmploymentTypes(parseCSV(preferencesData.preferredEmploymentType));
        }
      };
      dispatch(setPageSaved("preferences"));
      initializeFormFields();
    }
  }, [session?.user?.id, status]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }

    const employmentCsv = toCSV(employmentTypes);

    const dto: JsPreferencesDTO = {
      userId: session.user.id,
      targetedPathway: pathway,
      targetedPathwayId:
        preferencesData.targetedPathway !== pathway ? undefined : pathwayId,
      preferredEmploymentType: employmentCsv,
    };

    try {
      const response = await fetch(
        "/api/jobseekers/account/preferences/upsert",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(dto),
        },
      );

      if (response.ok) {
        const result = await response.json();
        devLog(JSON.stringify(result, null, 2));

        dispatch(setPageSaved("preferences"));
        dispatch(setPreferences({ ...preferencesData, ...dto }));

        router.push("/edit-profile/jobseeker/showcase");
      } else {
        const errorMessage = `Failed to submit preferences. Status: ${response.status} - ${response.statusText}`;
        setError(errorMessage);
      }
    } catch (e: any) {
      setError(`An unexpected error occurred: ${e.message}`);
    }
  }

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(2 / 6) * 100} />
        <p>Step 2/6</p>
        <h1>Your preferences</h1>

        <p className="subtitle">* Indicates a required field</p>
        <form onSubmit={handleSubmit}>
          <fieldset>
            <legend>What are you looking for?</legend>
            <Stack spacing={4}>
              <FormControl component="fieldset" variant="standard">
                <FormLabel component="legend" sx={{ color: "#000000ff" }}>
                  Select all that apply
                </FormLabel>
                <FormGroup>
                  {EMPLOYMENT_OPTIONS.map((label) => (
                    <FormControlLabel
                      key={label}
                      control={
                        <Checkbox
                          checked={employmentTypes.includes(label)}
                          onChange={(e) =>
                            toggleEmployment(label, e.target.checked)
                          }
                          name={label}
                        />
                      }
                      label={
                        label === "Full-time"
                          ? "Full-time job"
                          : label === "Part-time"
                            ? "Part-time job"
                            : label === "Internship"
                              ? "Internship"
                              : "On-campus job"
                      }
                      sx={{ mr: 2 }}
                    />
                  ))}
                </FormGroup>
              </FormControl>

              <FormControl component="fieldset" sx={{ mt: 4 }}>
                <FormLabel
                  id="profile-creation-preferences-require-role"
                  component="legend"
                  sx={{ color: "#000000ff" }}
                >
                  What technology path most interests you?
                </FormLabel>
                <RadioGroup
                  aria-labelledby="profile-creation-preferences-require-role"
                  name="profile-creation-preferences-require-role"
                  value={pathway}
                  onChange={(e) => setPathway(e.target.value)}
                >
                  {Object.values(CareerPrepPathways).map((pathValue) => (
                    <FormControlLabel
                      key={pathValue}
                      value={pathValue}
                      control={<Radio />}
                      label={pathValue}
                    />
                  ))}
                </RadioGroup>
              </FormControl>
            </Stack>
          </fieldset>

          <div className="profile-form-progress-btn-group">
            <PillButton
              variant="outlined"
              onClick={() =>
                router.push("/edit-profile/jobseeker/introduction")
              }
            >
              Previous
            </PillButton>
            <PillButton type="submit">Save and continue</PillButton>
          </div>
        </form>

        {error && <p style={{ color: "crimson", marginTop: 12 }}>{error}</p>}
      </section>
    </main>
  );
}
