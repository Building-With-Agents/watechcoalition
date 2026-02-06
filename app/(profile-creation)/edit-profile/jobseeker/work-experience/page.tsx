"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import {
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
} from "@mui/material";
import PillButton from "@/app/ui/components/PillButton";
import InputTextWithLabel from "../../../../ui/components/InputTextWithLabel";
import WorkExperiences, {
  defaultWorkExperienceData,
  WorkExperienceData,
} from "./form-field-groups/WorkExperiences";
import InternshipExperiences, {
  InternshipExperienceData,
} from "./form-field-groups/InternshipExperiences";
import { JsWorkExpDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/lib/jobseekerStore";
import {
  initialState,
  setWorkExperience,
} from "@/lib/features/profileCreation/jobseekerSlice";
import {
  setPageDirty,
  setPageSaved,
} from "@/lib/features/profileCreation/saveSlice";
import dayjs from "dayjs";
import _ from "lodash";
import { devLog } from "@/app/lib/utils";
import { Add } from "@mui/icons-material";

interface Data {
  yearsWorkExperience: string;
  monthsInternshipExperience: string | number;
  workExperiences: WorkExperienceData[];
  internshipExperiences: WorkExperienceData[];
  isAuthorizedToWorkUsa?: boolean | null;
  requiresSponsorship?: boolean | null;
  CareerPrepAssessment: {
    experienceWithInterview: boolean;
    experienceWithApplying: boolean;
  };
}

export default function CreateJobseekerProfileWorkExperiencePage() {
  const router = useRouter();
  const { data: session, status } = useSession();
  const dispatch = useDispatch();
  const originalWorkExperienceStoreData = useSelector(
    (state: RootState) => state.jobseeker.workExperience,
  );
  const workExperienceStoreData = useMemo(
    (): JsWorkExpDTO => ({
      ...originalWorkExperienceStoreData,
      workExperiences: originalWorkExperienceStoreData.workExperiences?.map(
        (workExperience) => ({
          ...workExperience,
          startDate: new Date(workExperience.startDate),
          endDate: workExperience.endDate
            ? new Date(workExperience.endDate)
            : null,
        }),
      ),
    }),
    [originalWorkExperienceStoreData],
  );
  let workExperienceData: JsWorkExpDTO = { ...workExperienceStoreData };
  const [error, setError] = useState<string | null>(null); // eslint-disable-line @typescript-eslint/no-unused-vars

  const [hasUnmetRequired, setHasUnmetRequired] = useState("");

  const initFilteredWorkExp =
    workExperienceData.workExperiences
      ?.filter((exp) => !exp.isInternship)
      .map(
        (exp): WorkExperienceData => ({
          workId: exp.workId,
          company: exp.company,
          sectorObject: {
            industry_sector_id: exp.sectorId ?? "",
            sector_title: "",
          },
          techAreaObject: { id: exp.techAreaId ?? "", title: "" },
          jobTitle: exp.jobTitle,
          startDate: !Boolean(exp.startDate) ? null : dayjs(exp.startDate),
          endDate: !Boolean(exp.endDate) ? null : dayjs(exp.endDate),
          isCurrentJob: exp.isCurrentJob,
          responsibilities: exp.responsibilities,
        }),
      ) ?? [];

  const initFilteredInternshipExp =
    workExperienceData.workExperiences
      ?.filter((exp) => exp.isInternship)
      .map(
        (exp): WorkExperienceData => ({
          workId: exp.workId,
          company: exp.company,
          sectorObject: {
            industry_sector_id: exp.sectorId ?? "",
            sector_title: "",
          },
          techAreaObject: { id: exp.techAreaId ?? "", title: "" },
          jobTitle: exp.jobTitle,
          startDate: !Boolean(exp.startDate) ? null : dayjs(exp.startDate),
          endDate: !Boolean(exp.endDate) ? null : dayjs(exp.endDate),
          isCurrentJob: exp.isCurrentJob,
          responsibilities: exp.responsibilities,
        }),
      ) ?? [];

  const [hasWorkExp, setHasWorkExp] = useState<boolean | null>(
    initFilteredWorkExp.length > 0 ? true : null,
  );
  const [hasInternshipExp, setHasInternshipExp] = useState<boolean | null>(
    initFilteredInternshipExp.length > 0 ? true : null,
  );

  const [data, setData] = useState<Data>({
    yearsWorkExperience: workExperienceData.yearsWorkExperience,
    monthsInternshipExperience:
      workExperienceData.monthsInternshipExperience ?? "",
    workExperiences: initFilteredWorkExp,
    internshipExperiences: initFilteredInternshipExp,
    isAuthorizedToWorkUsa: workExperienceData.isAuthorizedToWorkUsa,
    requiresSponsorship: workExperienceData.requiresSponsorship,
    CareerPrepAssessment: {
      experienceWithApplying:
        workExperienceData.CareerPrepAssessment.experienceWithApplying,
      experienceWithInterview:
        workExperienceData.CareerPrepAssessment.experienceWithInterview,
    },
  });

  function removeAllWorkExperiences() {
    setData({
      ...data,
      workExperiences: [],
    });
    dispatch(setPageDirty("work-experience"));
  }

  function removeAllInternshipExperiences() {
    setData({
      ...data,
      internshipExperiences: [],
    });
    dispatch(setPageDirty("work-experience"));
  }

  function addNewWorkExperience() {
    const newWorkExperienceData = defaultWorkExperienceData();
    setData({
      ...data,
      workExperiences: [...data.workExperiences, newWorkExperienceData],
    });
    dispatch(setPageDirty("work-experience"));
  }

  function removeWorkExperience(byUid: string) {
    setData({
      ...data,
      workExperiences: data.workExperiences.filter(
        ({ workId: uid }) => uid !== byUid,
      ),
    });
    dispatch(setPageDirty("work-experience"));
  }

  function addNewInternshipExperience() {
    const newInternshipExperienceData = defaultWorkExperienceData();
    setData({
      ...data,
      internshipExperiences: [
        ...data.internshipExperiences,
        newInternshipExperienceData,
      ],
    });
    dispatch(setPageDirty("work-experience"));
  }

  function removeInternshipExperience(byUid: string) {
    setData({
      ...data,
      internshipExperiences: data.internshipExperiences.filter(
        ({ workId: uid }) => uid !== byUid,
      ),
    });
    dispatch(setPageDirty("work-experience"));
  }

  const handleUpdate = useCallback(
    (key: string, value: any) => {
      setData((prevData) => ({
        ...prevData,
        [key]: value,
      }));
      dispatch(setPageDirty("work-experience"));
    },
    [dispatch],
  );

  const handleInputUpdate = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value, type } = event.target;
      setData((prevData) => ({
        ...prevData,
        [name]: type === "radio" ? value === "yes" : value, // setting boolean values for radio type
      }));
      dispatch(setPageDirty("work-experience"));
    },
    [dispatch],
  );

  const handleNestedInputUpdate = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const { name, value, type } = event.target;
      const newValue = type === "radio" ? value === "true" : value;

      setData((prevData) => {
        if (name.includes(".")) {
          const [parentKey, childKey] = name.split(".");
          if (parentKey === "CareerPrepAssessment") {
            return {
              ...prevData,
              CareerPrepAssessment: {
                ...prevData.CareerPrepAssessment,
                [childKey]: newValue,
              },
            };
          }

          return prevData;
        }
        return {
          ...prevData,
          [name as keyof typeof prevData]: newValue,
        };
      });

      dispatch(setPageDirty("work-experience"));
    },
    [dispatch],
  );

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(workExperienceStoreData, initialState.workExperience)) {
          const { id } = session.user;

          try {
            devLog("fetching fresh");
            const response = await fetch(
              "/api/jobseekers/account/work-info/get/" + id,
            );

            if (!response.ok) {
              workExperienceData.userId = id!;
            } else {
              const fetchedData: JsWorkExpDTO = (await response.json()).result;
              workExperienceData = {
                ...fetchedData,
              };
            }

            const filteredWorkExp =
              workExperienceData.workExperiences
                ?.filter((exp) => !exp.isInternship)
                .map(
                  (exp): WorkExperienceData => ({
                    workId: exp.workId,
                    company: exp.company,
                    sectorObject: {
                      industry_sector_id: exp.sectorId ?? "",
                      sector_title: "",
                    },
                    techAreaObject: { id: exp.techAreaId ?? "", title: "" },
                    jobTitle: exp.jobTitle,
                    startDate: dayjs(exp.startDate),
                    endDate: exp.endDate ? dayjs(exp.endDate) : null,
                    isCurrentJob: exp.isCurrentJob,
                    responsibilities: exp.responsibilities,
                  }),
                ) ?? [];

            const filteredInternshipExp =
              workExperienceData.workExperiences
                ?.filter((exp) => exp.isInternship)
                .map(
                  (exp): WorkExperienceData => ({
                    workId: exp.workId,
                    company: exp.company,
                    sectorObject: {
                      industry_sector_id: exp.sectorId ?? "",
                      sector_title: "",
                    },
                    techAreaObject: { id: exp.techAreaId ?? "", title: "" },
                    jobTitle: exp.jobTitle,
                    startDate: dayjs(exp.startDate),
                    endDate: exp.endDate ? dayjs(exp.endDate) : null,
                    isCurrentJob: exp.isCurrentJob,
                    responsibilities: exp.responsibilities,
                  }),
                ) ?? [];

            if (filteredWorkExp.length !== 0) setHasWorkExp(true);
            if (filteredInternshipExp.length !== 0) setHasInternshipExp(true);

            setData({
              yearsWorkExperience: workExperienceData.yearsWorkExperience,
              monthsInternshipExperience:
                workExperienceData.monthsInternshipExperience ?? "",
              workExperiences: filteredWorkExp,
              internshipExperiences: filteredInternshipExp,
              isAuthorizedToWorkUsa: workExperienceData.isAuthorizedToWorkUsa,
              requiresSponsorship: workExperienceData.requiresSponsorship,
              CareerPrepAssessment: {
                experienceWithApplying:
                  workExperienceData.CareerPrepAssessment
                    .experienceWithApplying,
                experienceWithInterview:
                  workExperienceData.CareerPrepAssessment
                    .experienceWithInterview,
              },
            });
          } catch (error) {
            console.error(error);
          }
        } else {
          devLog("fetching from store");
        }
      };
      initializeFormFields();
      dispatch(setPageSaved("work-experience"));
    }
  }, [session?.user?.id]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }

    const userId = session.user.id!;
    const jobseekerId = session.user.jobseekerId!;
    const workExperiences = data.workExperiences?.map((workExp) => ({
      workId: workExp.workId, //fixme: generate uuid on the backend or is this fine?
      jobseekerId: jobseekerId,
      techAreaId: workExp.techAreaObject.id,
      sectorId: workExp.sectorObject.industry_sector_id,
      company: workExp.company,
      isInternship: false,
      jobTitle: workExp.jobTitle,
      isCurrentJob: workExp.isCurrentJob,
      startDate: workExp.startDate ? workExp.startDate.toDate() : null,
      endDate: workExp.endDate ? workExp.endDate.toDate() : null,
      responsibilities: workExp.responsibilities,
    }));

    // Validate the work experience entries
    if (
      !workExperiences.every((workExperience) => {
        if (!Boolean(workExperience.startDate)) {
          setHasUnmetRequired(`${workExperience.workId}-startDate`);
          return false;
        }
        if (
          !Boolean(workExperience.endDate) &&
          !Boolean(workExperience.isCurrentJob)
        ) {
          setHasUnmetRequired(`${workExperience.workId}-endDate`);
          return false;
        }
        return true;
      })
    ) {
      return;
    }

    const internshipExperiences = data.internshipExperiences?.map(
      (internshipExp) => ({
        workId: internshipExp.workId,
        jobseekerId: jobseekerId,
        techAreaId: internshipExp.techAreaObject.id,
        sectorId: internshipExp.sectorObject.industry_sector_id,
        company: internshipExp.company,
        isInternship: true,
        jobTitle: internshipExp.jobTitle,
        isCurrentJob: internshipExp.isCurrentJob,
        startDate: internshipExp.startDate
          ? internshipExp.startDate.toDate()
          : null,
        endDate: internshipExp.endDate ? internshipExp.endDate.toDate() : null,
        responsibilities: internshipExp.responsibilities,
      }),
    );

    // Validate the internship experience entries
    if (
      !internshipExperiences.every((internshipExperience) => {
        if (!Boolean(internshipExperience.startDate)) {
          setHasUnmetRequired(`${internshipExperience.workId}-startDate`);
          return false;
        }
        if (!Boolean(internshipExperience.endDate)) {
          setHasUnmetRequired(`${internshipExperience.workId}-endDate`);
          return false;
        }
        return true;
      })
    ) {
      return;
    }

    workExperienceData.userId = userId;
    workExperienceData.yearsWorkExperience =
      data.yearsWorkExperience.toString(); // Replace with actual calculation
    workExperienceData.monthsInternshipExperience =
      data.monthsInternshipExperience.toString(); // Replace with actual calculation
    workExperienceData.isAuthorizedToWorkUsa = data.isAuthorizedToWorkUsa;
    workExperienceData.requiresSponsorship = data.requiresSponsorship;
    workExperienceData.CareerPrepAssessment = data.CareerPrepAssessment;
    workExperienceData.workExperiences = [
      ...(hasWorkExp ? workExperiences : []),
      ...(hasInternshipExp ? internshipExperiences : []),
    ].map((experience) => ({
      ...experience,
      startDate: experience.startDate ?? new Date(),
    }));

    try {
      const response = await fetch("/api/jobseekers/account/work-info/upsert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(workExperienceData),
      });

      if (response.ok) {
        dispatch(setPageSaved("work-experience"));
        dispatch(
          setWorkExperience({
            ...workExperienceData,
            workExperiences: workExperienceData.workExperiences?.map(
              (workExperience) => ({
                ...workExperience,
                startDate: workExperience.startDate.toISOString(),
                endDate: workExperience.endDate?.toISOString() ?? null,
              }),
            ),
          }),
        );
      } else {
        const errorMessage = `Failed to submit work experiences. Status: ${response.status} - ${response.statusText}`;
        setError(errorMessage);
      }

      await response.json();
      router.push("/edit-profile/jobseeker/disclosures");
    } catch (e: any) {
      setError(`An unexpected error occurred: ${e.message}`);
    }
  }

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(5 / 6) * 100} />
        <p>Step 5/6</p>
        <h1>Work experience</h1>
        <p>Complete these sections to improve your visibility to employers.</p>
        <p className="subtitle">* Indicates a required field</p>
        <form onSubmit={handleSubmit}>
          <fieldset className="work-experience-groups">
            <legend>
              <p>
                Share your professional journey, even if it's not tech-related.
                Employers value transferable skills like teamwork,
                communication, and problem-solving.
              </p>
              <h2>Work experience</h2>
            </legend>
            <RadioGroup>
              <p>Do you have any work experience? *</p>
              <div className="block gap-8">
                <Radio
                  name="hasWorkExp"
                  value="yes"
                  onChange={() => {
                    setHasWorkExp(true);
                    addNewWorkExperience();
                  }}
                  checked={hasWorkExp !== null && hasWorkExp}
                  required={true}
                />{" "}
                Yes
                <Radio
                  name="hasWorkExp"
                  value="no"
                  onChange={() => {
                    setHasWorkExp(false);
                    removeAllWorkExperiences();
                  }}
                  checked={hasWorkExp !== null && !hasWorkExp}
                  required={true}
                />{" "}
                No
              </div>
            </RadioGroup>
            <div className="profile-form-grid">
              <InputTextWithLabel
                type="number"
                id="profile-creation-experience-work-fulltime-years"
                name="yearsWorkExperience"
                value={data.yearsWorkExperience + ""}
                onChange={handleInputUpdate}
                hidden={!hasWorkExp}
                required={hasWorkExp}
              >
                How many years of work experience do you have (not including
                internship, enter 0 if none)?
              </InputTextWithLabel>
            </div>
            {hasWorkExp && (
              <WorkExperiences
                data={data.workExperiences}
                hasUnmetRequired={hasUnmetRequired}
                onUpdate={handleUpdate}
                onRemove={removeWorkExperience}
              />
            )}
            <PillButton
              variant="outlined"
              onClick={addNewWorkExperience}
              hidden={!hasWorkExp}
            >
              <Add className="mr-2 h-5 w-5" />
              Add work experience
            </PillButton>
          </fieldset>
          <fieldset className="internship-experience-groups">
            <legend>
              <p>
                Internships demonstrate your commitment to learning and growth.
                Highlight your hands-on experience and how it's prepared you for
                your career.
              </p>
              <h2>Internship experience</h2>
            </legend>
            <RadioGroup>
              <p>Do you have any internship experience? *</p>
              <div className="block gap-8">
                <Radio
                  name="hasInternExp"
                  value="yes"
                  onChange={() => {
                    setHasInternshipExp(true);
                    addNewInternshipExperience();
                  }}
                  checked={hasInternshipExp !== null && hasInternshipExp}
                  required={true}
                />{" "}
                Yes
                <Radio
                  name="hasInternExp"
                  value="no"
                  onChange={() => {
                    setHasInternshipExp(false);
                    removeAllInternshipExperiences();
                  }}
                  checked={hasInternshipExp !== null && !hasInternshipExp}
                  required={true}
                />{" "}
                No
              </div>
            </RadioGroup>
            <div className="profile-form-grid">
              <InputTextWithLabel
                type="number"
                id="profile-creation-experience-internship-months"
                name="monthsInternshipExperience"
                onChange={handleInputUpdate}
                value={data.monthsInternshipExperience + ""}
                required={hasInternshipExp}
                hidden={!hasInternshipExp}
              >
                How many months of internship work experience do you have?
              </InputTextWithLabel>
            </div>
            {hasInternshipExp && (
              <InternshipExperiences
                data={data.internshipExperiences as InternshipExperienceData[]}
                hasUnmetRequired={hasUnmetRequired}
                onUpdate={handleUpdate}
                onRemove={removeInternshipExperience}
              />
            )}
            <PillButton
              variant="outlined"
              onClick={addNewInternshipExperience}
              hidden={!hasInternshipExp}
            >
              <Add className="mr-2 h-5 w-5" />
              Add internship experience
            </PillButton>
          </fieldset>
          <h2>Job Readiness</h2>
          <div className="profile-form-grid">
            <FormControl component="fieldset">
              <p>Do you have have experience interviewing?</p>
              <RadioGroup
                name="CareerPrepAssessment.experienceWithInterview"
                onChange={handleNestedInputUpdate}
                value={data.CareerPrepAssessment.experienceWithInterview}
              >
                <FormControlLabel
                  value={true}
                  control={<Radio />}
                  label="Yes"
                />
                <FormControlLabel
                  value={false}
                  control={<Radio />}
                  label="No"
                />
              </RadioGroup>
            </FormControl>
            <FormControl component="fieldset">
              <p>Do you have experience applying for tech jobs?</p>
              <RadioGroup
                name="CareerPrepAssessment.experienceWithApplying"
                onChange={handleNestedInputUpdate}
                value={data.CareerPrepAssessment.experienceWithApplying}
              >
                <FormControlLabel
                  value={true}
                  control={<Radio />}
                  label="Yes"
                />
                <FormControlLabel
                  value={false}
                  control={<Radio />}
                  label="No"
                />
              </RadioGroup>
            </FormControl>
          </div>
          <fieldset>
            <legend>
              <h2>Authorization</h2>
            </legend>
            <p>
              Note: All work authorization information you provide will only be
              used for the purpose of verifying your qualifications for this job
              application and will not be disclosed to public view or any third
              parties without your express consent.
            </p>
            <div>
              <div className="mt-3">
                Are you authorized to work in the United States? *
              </div>
              <RadioGroup>
                <div className="block">
                  <Radio
                    name="isAuthorizedToWorkUsa"
                    value="yes"
                    onChange={handleInputUpdate}
                    checked={
                      typeof data.isAuthorizedToWorkUsa === "boolean"
                        ? data.isAuthorizedToWorkUsa
                        : false
                    }
                    required
                  />{" "}
                  Yes
                </div>
                <div className="block">
                  <Radio
                    name="isAuthorizedToWorkUsa"
                    value="no"
                    onChange={handleInputUpdate}
                    checked={
                      typeof data.isAuthorizedToWorkUsa === "boolean"
                        ? !data.isAuthorizedToWorkUsa
                        : false
                    }
                    required
                  />{" "}
                  No
                </div>
              </RadioGroup>
            </div>
            <div>
              <h3 className="alert-title">United States of America</h3>
              <p>
                Will you, now or in the future, require sponsorship for
                employment visa status? *
              </p>
              <RadioGroup>
                <div className="block">
                  <Radio
                    name="requiresSponsorship"
                    value="yes"
                    onChange={handleInputUpdate}
                    checked={
                      typeof data.requiresSponsorship === "boolean"
                        ? data.requiresSponsorship
                        : false
                    }
                    required
                  />{" "}
                  Yes
                </div>
                <div className="block">
                  <Radio
                    name="requiresSponsorship"
                    value="no"
                    onChange={handleInputUpdate}
                    checked={
                      typeof data.requiresSponsorship === "boolean"
                        ? !data.requiresSponsorship
                        : false
                    }
                    required
                  />{" "}
                  No
                </div>
              </RadioGroup>
            </div>
          </fieldset>
          <div className="profile-form-progress-btn-group">
            <PillButton
              variant="outlined"
              onClick={() => {
                router.push("/edit-profile/jobseeker/education");
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
