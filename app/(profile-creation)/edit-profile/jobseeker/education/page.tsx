"use client";

import React, { ChangeEvent, useCallback, useEffect, useState } from "react";
import SelectOptionsWithLabel from "@/app/ui/components/SelectOptionsWithLabel";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import PillButton from "@/app/ui/components/PillButton";
import { Radio, RadioGroup } from "@mui/material";
import {
  CertDTO,
  HighestCompletedEducationLevel,
  EducationLevel,
  JsEducationInfoDTO,
  JsEducationPageDTO,
  ProjectExpDTO,
  CollegeDegreeType,
  HighSchoolDegreeType,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { useRouter } from "next/navigation";

import Educations, {
  defaultEducationData,
  EducationData,
} from "./form-field-groups/Educations";
import Licenses, {
  defaultLicenseData,
  LicenseData,
} from "./form-field-groups/Licenses";
import ProjectExperiences, {
  defaultProjectExperienceData,
  ProjectExperienceData,
} from "./form-field-groups/ProjectExperiences";
import { devLog, mapToEnum, mapToEnumOrThrow } from "@/app/lib/utils";
import { useSession } from "next-auth/react";
import { useDispatch, useSelector } from "react-redux";
import { RootState } from "@/lib/jobseekerStore";
import {
  initialState,
  setEducation,
} from "@/lib/features/profileCreation/jobseekerSlice";
import {
  setPageDirty,
  setPageSaved,
} from "@/lib/features/profileCreation/saveSlice";
import dayjs from "dayjs";
import _ from "lodash";
import { Add } from "@mui/icons-material";
import {
  FormControl,
  FormLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import { TimeUntilCompletion } from "@/app/lib/admin/careerPrep";

interface Data {
  projectExperiences: ProjectExperienceData[];
  licenses: LicenseData[];
  educations: EducationData[];
}

export default function CreateJobseekerProfileEducationPage() {
  const router = useRouter();
  const { data: session, status } = useSession(); // Use useSession hook and destructure update
  const dispatch = useDispatch();
  const educationStoreData = useSelector(
    (state: RootState) => state.jobseeker.education,
  );
  let educationData = { ...educationStoreData };
  const [error, setError] = useState<string | null>(null); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [hasUnmetRequired, setHasUnmetRequired] = useState("");

  const [highestLevelOfStudy, setHighestLevelOfStudy] = useState(
    educationData.highestLevelOfStudy,
  );

  const [hasEduHistory, setHasEduHistory] = useState<boolean | null>(
    educationData.educations.length > 0 ? true : null,
  );
  const [hasCerts, setHasCerts] = useState<boolean | null>(
    educationData.certifications.length > 0 ? true : null,
  );
  const [expectedEduCompletion, setExpectedEduCompletion] = useState(
    educationData.CareerPrepAssessment.expectedEduCompletion,
  );
  const [data, setData] = useState<Data>({
    projectExperiences: educationData.projects.map(
      (project): ProjectExperienceData => ({
        projectId: project.projectId,
        projectTitle: project.projTitle,
        projectRole: project.projectRole,
        startDate: !Boolean(project.startDate)
          ? null
          : dayjs(project.startDate),
        completionDate: !Boolean(project.completionDate)
          ? null
          : dayjs(project.completionDate),
        reference: project.repoUrl ?? "",
        problemSolvedDescription: project.problemSolvedDescription,
        teamSize: project.teamSize,
        skills: project.skills,
        fetchedSkills: project.skills,
      }),
    ),
    licenses: educationData.certifications.map(
      (cert): LicenseData => ({
        certId: cert.certId,
        name: cert.name,
        issuingOrg: cert.issuingOrg,
        credentialId: cert.credentialId ?? "",
        credentialUrl: cert.credentialUrl ?? "",
        issueDate: !Boolean(cert.issueDate) ? null : dayjs(cert.issueDate),
        expiryDate: !Boolean(cert.expiryDate) ? null : dayjs(cert.expiryDate),
      }),
    ),
    educations: educationData.educations.map(
      (education: JsEducationInfoDTO): EducationData => ({
        id: education.id,
        edLevel: education.edLevel ?? EducationLevel.Unselected,
        edProviderObject: {
          id: education.edProviderId ?? "",
          name: education.edProviderName ?? "",
        },
        edProviderId: education.edProviderId,
        edProviderName: education.edProviderName ?? "",
        isEnrolled: education.isEnrolled,
        enrollmentStatus: education.enrollmentStatus,
        startDate: !Boolean(education.startDate)
          ? null
          : dayjs(education.startDate),
        gradDate: !Boolean(education.gradDate)
          ? null
          : dayjs(education.gradDate),
        degreeType:
          mapToEnum(education.degreeType ?? null, HighSchoolDegreeType) ??
          mapToEnumOrThrow(education.degreeType ?? null, CollegeDegreeType),
        programObject:
          education.programId && education.programName
            ? {
                id: education.programId,
                title: education.programName,
              }
            : undefined,
        programName: education.programName,
        programId: education.programId,
        preAppEdSystem: education.preAppEdSystem,
        description: education.description,
        gpa: education.gpa,
        isTechDegree: undefined,
      }),
    ),
  });

  function removeAllCerts() {
    setData({
      ...data,
      licenses: [],
    });
    dispatch(setPageDirty("education"));
  }

  function removeAllEduHistory() {
    setData({
      ...data,
      educations: [],
    });
    dispatch(setPageDirty("education"));
  }

  function handleLevelOfStudy(event: ChangeEvent<HTMLSelectElement>) {
    setHighestLevelOfStudy(
      mapToEnumOrThrow(event.target.value, HighestCompletedEducationLevel),
    );
    dispatch(setPageDirty("education"));
  }

  function handleExpectedEduCompletion(event: SelectChangeEvent<string>) {
    setExpectedEduCompletion(
      mapToEnumOrThrow(event.target.value, TimeUntilCompletion),
    );
    dispatch(setPageDirty("education"));
  }

  function addNewLicense() {
    const newLicenseData = defaultLicenseData();
    setData({
      ...data,
      licenses: [...data.licenses, newLicenseData],
    });
    dispatch(setPageDirty("education"));
  }

  function removeLicense(byUid: string) {
    setData({
      ...data,
      licenses: data.licenses.filter(({ certId: uid }) => uid !== byUid),
    });
    dispatch(setPageDirty("education"));
  }

  function addNewProjectExperience() {
    const newProjectExperienceData = defaultProjectExperienceData();
    setData({
      ...data,
      projectExperiences: [
        ...data.projectExperiences,
        newProjectExperienceData,
      ],
    });
    dispatch(setPageDirty("education"));
  }

  function removeProjectExperience(byUid: string) {
    setData({
      ...data,
      projectExperiences: data.projectExperiences.filter(
        ({ projectId: uid }) => uid !== byUid,
      ),
    });
    dispatch(setPageDirty("education"));
  }

  function addNewEducation() {
    const newEducationData = defaultEducationData();
    setData({
      ...data,
      educations: [...data.educations, newEducationData],
    });
    dispatch(setPageDirty("education"));
  }

  function removeEducation(byUid: string) {
    setData({
      ...data,
      educations: data.educations.filter(({ id: uid }) => uid !== byUid),
    });
    dispatch(setPageDirty("education"));
  }

  const handleUpdate = useCallback((key: string, value: any) => {
    setData((prevData) => ({
      ...prevData,
      [key]: value,
    }));
    dispatch(setPageDirty("education"));
  }, []);

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(educationStoreData, initialState.education)) {
          const { id, jobseekerId } = session.user;

          try {
            devLog("fetching fresh");
            const response = await fetch(
              "/api/jobseekers/account/edu-info/get/" + id,
            );

            if (!response.ok) {
              educationData.userId = id!;
              educationData.jobseekerId = jobseekerId!;
            } else {
              const fetchedData: JsEducationPageDTO = (await response.json())
                .result;
              educationData.userId = id!;
              educationData.jobseekerId = jobseekerId!;

              if (fetchedData.highestLevelOfStudy) {
                educationData.highestLevelOfStudy =
                  fetchedData.highestLevelOfStudy;
                setHighestLevelOfStudy(educationData.highestLevelOfStudy);
              }
              if (fetchedData.CareerPrepAssessment.expectedEduCompletion) {
                setExpectedEduCompletion(
                  fetchedData.CareerPrepAssessment.expectedEduCompletion,
                );
              }
              if (fetchedData.educations?.length !== 0) {
                educationData.educations = fetchedData.educations;
                setHasEduHistory(true);
              } else {
                educationData.educations = [
                  {
                    ...defaultEducationData(),
                    gradDate: "",
                    startDate: "",
                    programId: undefined,
                    edProviderId: "",
                    enrollmentStatus: undefined,
                  },
                ];
              }
              if (fetchedData.projects?.length !== 0) {
                educationData.projects = fetchedData.projects;
              }
              if (fetchedData.certifications?.length !== 0) {
                educationData.certifications = fetchedData.certifications;
                setHasCerts(true);
              } else {
                educationData.certifications = [
                  {
                    ...defaultLicenseData(),
                    issueDate: undefined,
                    expiryDate: undefined,
                  },
                ];
              }

              setData({
                ...data,
                educations: [
                  ...data.educations,
                  ...educationData.educations.map(
                    (education): EducationData => ({
                      id: education.id,
                      edLevel: education.edLevel ?? EducationLevel.Unselected,
                      edProviderObject: {
                        id: education.edProviderId ?? "",
                        name: education.edProviderName ?? "",
                      },
                      edProviderId: education.edProviderId,
                      edProviderName: education.edProviderName ?? "",
                      isEnrolled: education.isEnrolled,
                      enrollmentStatus: education.enrollmentStatus,
                      startDate: dayjs(education.startDate),
                      gradDate: dayjs(education.gradDate),
                      degreeType:
                        mapToEnum(
                          education.degreeType ?? null,
                          HighSchoolDegreeType,
                        ) ??
                        mapToEnumOrThrow(
                          education.degreeType ?? null,
                          CollegeDegreeType,
                        ),
                      programObject:
                        education.programId && education.programName
                          ? {
                              id: education.programId,
                              title: education.programName,
                            }
                          : undefined,
                      programName: education.programName,
                      programId: education.programId,
                      preAppEdSystem: education.preAppEdSystem,
                      description: education.description,
                      gpa: education.gpa,
                      isTechDegree: undefined,
                    }),
                  ),
                ],
                projectExperiences: [
                  ...data.projectExperiences,
                  ...educationData.projects.map(
                    (project): ProjectExperienceData => ({
                      projectId: project.projectId,
                      projectTitle: project.projTitle,
                      projectRole: project.projectRole,
                      startDate: project.startDate
                        ? dayjs(project.startDate)
                        : null,
                      completionDate: project.completionDate
                        ? dayjs(project.completionDate)
                        : null,
                      reference: project.repoUrl ?? "",
                      problemSolvedDescription:
                        project.problemSolvedDescription,
                      teamSize: project.teamSize,
                      skills: project.skills,
                      fetchedSkills: project.skills,
                    }),
                  ),
                ],
                licenses: [
                  ...data.licenses,
                  ...educationData.certifications.map(
                    (cert): LicenseData => ({
                      certId: cert.certId,
                      name: cert.name,
                      issuingOrg: cert.issuingOrg,
                      credentialId: cert.credentialId ?? "",
                      credentialUrl: cert.credentialUrl ?? "",
                      issueDate: cert.issueDate ? dayjs(cert.issueDate) : null,
                      expiryDate: cert.expiryDate
                        ? dayjs(cert.expiryDate)
                        : null,
                    }),
                  ),
                ],
              });
            }
          } catch (error) {
            console.error(error);
          }
        } else {
          devLog("fetching from store");
        }
      };
      dispatch(setPageSaved("education"));
      initializeFormFields();
    }
  }, [session?.user?.id]);

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }

    setHasUnmetRequired("");

    const userId = session.user.id;

    const educations: JsEducationInfoDTO[] = data.educations.map(
      (ed: EducationData) => ({
        id: ed.id,
        edProviderId: ed?.edProviderObject?.id || ed?.edProviderId!,
        edLevel: ed.edLevel,
        edProviderName: ed?.edProviderObject?.name || ed?.edProviderName,
        isEnrolled: ed.isEnrolled,
        enrollmentStatus: ed.enrollmentStatus ?? undefined,
        startDate: ed.startDate?.toISOString() ?? "",
        gradDate: ed.gradDate?.toISOString() ?? "",
        degreeType: ed.degreeType || undefined,
        programId: ed?.programObject?.id || ed?.programId || undefined, // Note: no rel with provider_programs pulled from a separate programs table.
        programName: ed?.programObject?.title || ed?.programName || undefined,
        gpa: ed?.gpa,
        preAppEdSystem: ed.preAppEdSystem || null,
        description: ed.description || null,
        isTechnicalDegree: ed.isTechDegree || false,
      }),
    );

    // Validate the education entries
    if (
      !educations.every((education) => {
        if (
          !Boolean(education.edProviderId) &&
          !Boolean(education.edProviderName)
        ) {
          setHasUnmetRequired(`${education.id}-edProviderObject`);
          return false;
        }
        if (education.edLevel === EducationLevel.College) {
          if (
            !Boolean(education.programId) &&
            !Boolean(education.programName)
          ) {
            setHasUnmetRequired(`${education.id}-programObject`);
            return false;
          }
        }
        if (!Boolean(education.startDate)) {
          setHasUnmetRequired(`${education.id}-startDate`);
          return false;
        }
        if (!Boolean(education.gradDate)) {
          setHasUnmetRequired(`${education.id}-gradDate`);
          return false;
        }
        return true;
      })
    ) {
      return;
    }

    const certifications: CertDTO[] = data.licenses.map(
      (cert: LicenseData) => ({
        certId: cert.certId,
        name: cert.name,
        logoUrl: undefined,
        issuingOrg: cert.issuingOrg,
        credentialId: cert.credentialId,
        credentialUrl: cert.credentialUrl,
        issueDate: cert.issueDate?.toISOString() ?? undefined,
        expiryDate: cert.expiryDate?.toISOString() ?? undefined,
        description: undefined,
      }),
    );

    const projects: ProjectExpDTO[] = data.projectExperiences.map(
      (proj: ProjectExperienceData) => ({
        projectId: proj.projectId,
        projTitle: proj.projectTitle,
        projectRole: proj.projectRole,
        startDate: proj.startDate?.toISOString() ?? "",
        completionDate: proj.completionDate?.toISOString() ?? "",
        problemSolvedDescription: proj.problemSolvedDescription,
        teamSize: proj.teamSize,
        repoUrl: proj.reference,
        videoDemoUrl: undefined,
        skills: proj.skills,
      }),
    );

    // Validate the project experience entries
    if (
      !projects.every((project) => {
        if (project.skills.length === 0) {
          setHasUnmetRequired(`${project.projectId}-skills`);
          return false;
        }
        if (!Boolean(project.startDate)) {
          setHasUnmetRequired(`${project.projectId}-startDate`);
          return false;
        }
        if (!Boolean(project.completionDate)) {
          setHasUnmetRequired(`${project.projectId}-completionDate`);
          return false;
        }
        return true;
      })
    ) {
      return;
    }

    educationData = {
      ...educationData,
      userId: userId,
      highestLevelOfStudy: highestLevelOfStudy,
      CareerPrepAssessment: {
        expectedEduCompletion: expectedEduCompletion,
      },
      educations: educations,
      certifications: certifications,
      projects: projects,
    };

    try {
      const response = await fetch("/api/jobseekers/account/edu-info/upsert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(educationData),
      });

      if (response.ok) {
        const data = await response.json();
        devLog(JSON.stringify(data, null, 2));

        dispatch(setPageSaved("education"));
        dispatch(setEducation(educationData));

        router.push("/edit-profile/jobseeker/work-experience");
      } else {
        const errorMessage = await response.text(); // Get the error message from the response
        setError(`Failed to save data:\n${errorMessage}`);
      }
    } catch (e: any) {
      setError(`An unexpected error occurred: ${e.message}`);
    }
  };

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(4 / 6) * 100} />
        <p>Step 4/6</p>
        <h1>Education</h1>
        <p>
          The Talent Portal connects you to in-demand technical training through
          our coalition partners. Complete your training, and we'll connect you
          directly with employer partners actively seeking your skills. Whether
          you've completed a technical training program, are finishing a
          technical degree, or just starting your tech journey, we have
          resources to help you succeed.
        </p>
        <p className="subtitle">* Indicates a required field</p>
        <form onSubmit={handleSubmit}>
          <fieldset>
            <legend>
              <h2>Highest Level of Education</h2>
            </legend>
            <SelectOptionsWithLabel
              id="profile-creation-education-highest-completed"
              className="w-full"
              options={(
                Object.values(HighestCompletedEducationLevel) as string[]
              )
                .filter(
                  (value) => value !== "Certificate (less than two years)", // TODO: review to see if needs included for WJI grant reporting.
                )
                .map((value) => ({ label: value, value }))}
              placeholder="Please select"
              onChange={handleLevelOfStudy}
              value={highestLevelOfStudy}
              required={true}
            >
              What is the highest degree you’ve earned or schooling completed?
            </SelectOptionsWithLabel>
          </fieldset>
          <FormControl fullWidth component="fieldset" sx={{ mb: 2 }}>
            <FormLabel>When do you expect to finish your education?</FormLabel>
            <Select
              fullWidth
              id="expected-edu-completion"
              label="Estimated finish"
              value={expectedEduCompletion}
              onChange={handleExpectedEduCompletion}
            >
              {Object.entries(TimeUntilCompletion).map(([value, label]) => (
                <MenuItem key={value + label} id={value + label} value={label}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          <fieldset>
            <legend>
              <h2>Education History</h2>
            </legend>
            <RadioGroup>
              <p>Do you have an education history? *</p>
              <div className="block gap-8">
                <Radio
                  name="hasEduHistory"
                  value="yes"
                  onChange={() => {
                    setHasEduHistory(true);
                    addNewEducation();
                  }}
                  checked={hasEduHistory !== null && hasEduHistory}
                  required={true}
                />{" "}
                Yes
                <Radio
                  name="hasEduHistory"
                  value="no"
                  onChange={() => {
                    setHasEduHistory(false);
                    removeAllEduHistory();
                  }}
                  checked={hasEduHistory !== null && !hasEduHistory}
                  required={true}
                />{" "}
                No
              </div>
            </RadioGroup>
            {hasEduHistory && (
              <Educations
                data={data.educations}
                hasUnmetRequired={hasUnmetRequired}
                onUpdate={handleUpdate}
                onRemove={removeEducation}
              />
            )}
            <PillButton
              variant="outlined"
              onClick={addNewEducation}
              hidden={!hasEduHistory}
            >
              <Add className="mr-2 h-5 w-5" />
              Add education history
            </PillButton>
          </fieldset>
          <fieldset className="license-groups">
            <legend>
              <h2>Licenses &amp; Certifications</h2>
            </legend>
            <RadioGroup>
              <p>
                Have you completed a technical certification program with a
                provider outside of our coalition? *
              </p>
              <div className="block gap-8">
                <Radio
                  name="hasCerts"
                  value="yes"
                  onChange={() => {
                    setHasCerts(true);
                    addNewLicense();
                  }}
                  checked={hasCerts !== null && hasCerts}
                  required={true}
                />{" "}
                Yes
                <Radio
                  name="hasCerts"
                  value="no"
                  onChange={() => {
                    setHasCerts(false);
                    removeAllCerts();
                  }}
                  checked={hasCerts !== null && !hasCerts}
                  required={true}
                />{" "}
                No
              </div>
            </RadioGroup>
            {hasCerts && (
              <Licenses
                data={data.licenses}
                onUpdate={handleUpdate}
                onRemove={removeLicense}
              />
            )}
            <PillButton
              variant="outlined"
              onClick={addNewLicense}
              hidden={!hasCerts}
            >
              <Add className="mr-2 h-5 w-5" />
              Add license or certification
            </PillButton>
          </fieldset>
          <fieldset className="project-experience-groups">
            <legend>
              <h2>Project experience</h2>
              <p>
                Share your experience creating or contributing to a project as a
                student, apprentice, or intern.
              </p>
            </legend>
            <ProjectExperiences
              data={data.projectExperiences}
              hasUnmetRequired={hasUnmetRequired}
              onUpdate={handleUpdate}
              onRemove={removeProjectExperience}
            />
            <PillButton variant="outlined" onClick={addNewProjectExperience}>
              <Add className="mr-2 h-5 w-5" />
              Add project experience
            </PillButton>
          </fieldset>
          <div className="profile-form-progress-btn-group flex">
            <PillButton
              variant="outlined"
              onClick={() => {
                router.push("/edit-profile/jobseeker/showcase");
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
