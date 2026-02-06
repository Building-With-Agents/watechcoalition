import React, { memo, useCallback } from "react";
import InputTextWithLabel from "@/app/ui/components/InputTextWithLabel";
import SelectOptionsWithLabel from "@/app/ui/components/SelectOptionsWithLabel";
import PillButton from "@/app/ui/components/PillButton";
import {
  Radio,
  FormControl,
  FormLabel,
  FormControlLabel,
  RadioGroup,
} from "@mui/material";
import {
  CollegeDegreeType,
  HighSchoolDegreeType,
  EducationLevel,
  PreAEduSystem,
  ProgramEnrollmentStatus,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import TextFieldWithAutocomplete from "@/app/ui/components/mui/TextFieldWithAutocomplete";
import RequiredTooltip from "@/app/ui/components/mui/RequiredTooltip";
import { EducationProviderDTO } from "@/data/dtos/EducationProviderDTO";
import { GeneralProgramDTO } from "@/data/dtos/GeneralProgramDTO";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Dayjs } from "dayjs";
import { v4 as uuidv4 } from "uuid";
import { Close } from "@mui/icons-material";

const classNamePrefix = "profile-creation-education-group-";

const classEdLevel = "edLevel";
const classEdProviderObject = "edProviderObject"; // fixme edProviderObject
const classEdProviderId = "edProviderId";
const classEdProviderName = "edProviderName";
const classIsCurrent = "isEnrolled";
const classStartDate = "startDate";
const classEndDate = "gradDate";
const classDegreeType = "degreeType";
const classEnrollmentStatus = "enrollmentStatus";
// const classGradeLevel = "schoolGradeLevel"; no longer needed as an input
// const classPreALevel = "preALevel";
const classProgramObject = "programObject"; // fixme: rename to programId
const classProgramName = "programName";
const classProgramId = "programId";
// const classMajor = "major";
// const classMinor = "minor";
const classPreAppEdSystem = "preAppEdSystem";
const classDescription = "description";
const classGPA = "gpa";
const classIsTechDegree = "isTechDegree";

export interface EducationData {
  id: string;
  [classEdLevel]: EducationLevel;
  [classEdProviderName]: string;
  [classIsCurrent]: boolean;
  [classStartDate]: Dayjs | null;
  [classEndDate]: Dayjs | null;
  // [classGradeLevel]: string,
  [classEdProviderObject]?: EducationProviderDTO | null;
  [classEdProviderId]?: string | null;
  [classDegreeType]?: CollegeDegreeType | HighSchoolDegreeType | null;
  [classEnrollmentStatus]?: ProgramEnrollmentStatus | null;
  [classProgramObject]?: GeneralProgramDTO | null;
  [classProgramName]?: string;
  [classProgramId]?: string | null;
  // [classMajor]?: string | null, //TODO:  replaced with program
  // [classMinor]?: string | null,
  [classPreAppEdSystem]?: PreAEduSystem | null;
  [classDescription]?: string | null;
  [classGPA]?: string | null;
  [classIsTechDegree]?: boolean;
}

export function defaultEducationData() {
  return {
    id: uuidv4(),
    [classEdLevel]: EducationLevel.Unselected,
    [classEdProviderObject]: null,
    [classEdProviderId]: null,
    [classEdProviderName]: "",
    [classIsCurrent]: false,
    [classStartDate]: null,
    [classEndDate]: null,
    [classDegreeType]: null,
    [classEnrollmentStatus]: null,
    // [classGradeLevel]: null,
    // [classPreALevel]: null,
    [classProgramObject]: null,
    [classProgramId]: null,
    [classProgramName]: "",
    // [classMajor]: "",
    // [classMinor]: "",
    [classPreAppEdSystem]: null,
    [classDescription]: "",
    [classGPA]: null,
    [classIsTechDegree]: undefined,
  };
}

interface Props {
  data: EducationData[];
  hasUnmetRequired: string;
  onRemove: (uid: string) => void;
  onUpdate: (key: string, value: any) => void;
}

export default memo(function Educations({
  data,
  hasUnmetRequired,
  onRemove,
  onUpdate,
}: Props) {
  const handleChange = useCallback(
    <K extends keyof EducationData>(index: number, key: K, value: any) => {
      const changedEducations: EducationData[] = [...data];
      const updatedEducation = changedEducations[index];
      updatedEducation[key] = value;
      if (key === classEdProviderObject) {
        if (typeof value === "string") {
          updatedEducation[classEdProviderName] = value;
          updatedEducation[classEdProviderId] = uuidv4();
        } else if (value) {
          updatedEducation[classEdProviderName] = value.name;
          updatedEducation[classEdProviderId] = value.id;
        } else {
          updatedEducation[classEdProviderName] = "";
          updatedEducation[classEdProviderId] = null;
        }
      } else if (key === classProgramObject) {
        if (typeof value === "string") {
          updatedEducation[classProgramName] = value;
          updatedEducation[classProgramId] = uuidv4();
        } else if (value) {
          updatedEducation[classProgramName] = value.title;
          updatedEducation[classProgramId] = value.id;
        } else {
          updatedEducation[classProgramName] = "";
          updatedEducation[classProgramId] = null;
        }
      }
      onUpdate("educations", changedEducations);
    },
    [data, onUpdate],
  );

  return data.map((education, index) => (
    <fieldset key={classNamePrefix + education.id + "-key"}>
      <legend className="flex w-full justify-between">
        <h3>Education History {index + 1}</h3>
        <PillButton onClick={() => onRemove(education.id)} variant="outlined">
          <Close className="h-5 w-5" />
        </PillButton>
      </legend>

      <div>
        <p>
          If you have completed technical training through one of our coalition
          partners, select <strong>Technical Training Program</strong> below:
        </p>
        <div className="mt-4 grid grid-cols-3 mb-4">
          <li>Ada Developers Academy</li>
          <li>Big Bend Community College</li>
          <li>Career Connect SW ESD 112</li>
          <li>CodeDay x MinT</li>
          <li>Computing For All</li>
          <li>Per Scholas</li>
          <li>PNW Cyber Challenge Games</li>
          <li>Riipen</li>
          <li>SkillSource</li>
          <li>Washington Vets to Tech</li>
          <li>Wenatchee Valley College</li>
          <li>Year Up Puget Sound</li>
        </div>
        <FormControl component="fieldset">
          <FormLabel
            className="mb-2 mt-5"
            id="profile-creation-education-currently-enrolled-label"
            component="legend"
            sx={{ color: "#000000ff" }}
          >
            Type of school or program: *
          </FormLabel>
          <RadioGroup
            aria-labelledby="profile-creation-education-currently-enrolled-label"
            value={education[classEdLevel]}
            onChange={(e) => handleChange(index, classEdLevel, e.target.value)}
            name="profile-creation-education-currently-enrolled"
          >
            <FormControlLabel
              value={EducationLevel.HighSchool}
              control={<Radio required />}
              label="High school"
              sx={{
                "& .MuiFormControlLabel-asterisk": {
                  display: "none",
                },
              }}
            />
            <FormControlLabel
              value={EducationLevel.College}
              control={<Radio required />}
              label="College"
              sx={{
                "& .MuiFormControlLabel-asterisk": {
                  display: "none",
                },
              }}
            />
            <FormControlLabel
              value={EducationLevel.TrainingProgram}
              control={<Radio required />}
              label="Technical Training Program"
              sx={{
                "& .MuiFormControlLabel-asterisk": {
                  display: "none",
                },
              }}
            />
            <FormControlLabel
              value={EducationLevel.PreApprenticeship}
              control={<Radio required />}
              label="Pre-apprenticeship"
              sx={{
                "& .MuiFormControlLabel-asterisk": {
                  display: "none",
                },
              }}
            />
            <FormControlLabel
              value={EducationLevel.Other}
              control={<Radio required />}
              label="Other"
              sx={{
                "& .MuiFormControlLabel-asterisk": {
                  display: "none",
                },
              }}
            />
          </RadioGroup>
        </FormControl>
      </div>
      {education[classEdLevel] !== EducationLevel.HighSchool ? (
        ""
      ) : (
        <div id="profile-creation-education-high-school-fields">
          <div className="profile-form-grid">
            <RequiredTooltip
              open={
                hasUnmetRequired ===
                  `${education.id}-${classEdProviderObject}` &&
                !Boolean(education[classEdProviderObject])
              }
              errorMessage="A high school name is required"
            >
              <TextFieldWithAutocomplete
                apiSearchRoute="/api/edu-providers/search/"
                fieldLabel="Name of high school: *"
                id="profile-creation-education-high-school-name"
                searchingText="Searching..."
                noResultsText="No education providers found..."
                value={education[classEdProviderObject] ?? ""}
                onChange={(e, val) =>
                  handleChange(index, classEdProviderObject, val)
                }
                searchPlaceholder="Example: Chief Sealth High School"
                getOptionLabel={(option: EducationProviderDTO) =>
                  option.name ?? ""
                }
              />
            </RequiredTooltip>
            <TextFieldWithAutocomplete
              apiSearchRoute="/api/edu-providers/programs/high-school/search/"
              fieldLabel="What is your program?"
              id="profile-creation-education-high-school-program"
              searchingText="Searching..."
              noResultsText="No education provider programs found..."
              value={education[classProgramObject] ?? ""}
              onChange={(e, val) =>
                handleChange(index, classProgramObject, val)
              }
              searchPlaceholder="Program name"
              getOptionLabel={(option: GeneralProgramDTO) => option.title ?? ""}
            />
            <SelectOptionsWithLabel
              id="profile-creation-education-high-school-degree"
              className="w-full"
              options={(Object.values(HighSchoolDegreeType) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classDegreeType, e.target.value)
              }
              value={education[classDegreeType] as string}
            >
              Type of degree earned:
            </SelectOptionsWithLabel>

            {/*added for WJI data collection alignment (Please do not modify data).*/}
            <SelectOptionsWithLabel
              id="profile-creation-education-enrollment-status"
              className="w-full"
              options={(Object.values(ProgramEnrollmentStatus) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classEnrollmentStatus, e.target.value)
              }
              required
              value={education[classEnrollmentStatus] as string}
            >
              Enrollment status: *
            </SelectOptionsWithLabel>
            {/*end add for WJI data collection alignment*/}
          </div>
          <div className="profile-form-grid md:grid-cols-2">
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classStartDate}` &&
                !Boolean(education[classStartDate])
              }
              errorMessage="A starting date is required"
            >
              <DatePicker
                label={"Starting date *"}
                views={["month", "year"]}
                value={education[classStartDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(
                    index,
                    classStartDate,
                    val?.isValid() ? val : null,
                  )
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classEndDate}` &&
                !Boolean(education[classEndDate])
              }
              errorMessage="A completion date is required"
            >
              <DatePicker
                label={"Completion date *"}
                views={["month", "year"]}
                value={education[classEndDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(index, classEndDate, val?.isValid() ? val : null)
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
          </div>
          {/*  <Checkbox*/}
          {/*    id={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    name={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    checked={education[classIsCurrent]}*/}
          {/*    onChange={(e) =>*/}
          {/*      handleChange(index, classIsCurrent, e.target.checked)*/}
          {/*    }*/}
          {/*  />*/}
          {/*  Current*/}
          <div className="profile-form-grid">
            <InputTextWithLabel
              id={"profile-creation-education-high-school-gpa"}
              type="text"
              className="w-full"
              placeholder="Example: 4.0"
              onChange={(e) => handleChange(index, classGPA, e.target.value)}
              value={education[classGPA] ?? ""}
            >
              Grade Point Average (GPA):
            </InputTextWithLabel>
          </div>
        </div>
      )}
      {education[classEdLevel] !== EducationLevel.College ? (
        ""
      ) : (
        <div id="profile-creation-education-college-fields">
          <div className="profile-form-grid">
            <RequiredTooltip
              open={
                hasUnmetRequired ===
                  `${education.id}-${classEdProviderObject}` &&
                !Boolean(education[classEdProviderObject])
              }
              errorMessage="A college name is required"
            >
              <TextFieldWithAutocomplete
                apiSearchRoute="/api/edu-providers/search/"
                fieldLabel="Name of college: *"
                id="profile-creation-education-college-name"
                searchingText="Searching..."
                noResultsText="No education providers found..."
                value={education[classEdProviderObject] ?? ""}
                onChange={(e, val) =>
                  handleChange(index, classEdProviderObject, val)
                }
                searchPlaceholder="Example: University of Washington"
                getOptionLabel={(option: EducationProviderDTO) =>
                  option.name ?? ""
                }
              />
            </RequiredTooltip>
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classProgramObject}` &&
                !Boolean(education[classProgramObject])
              }
              errorMessage="A college major or concentration is required"
            >
              <TextFieldWithAutocomplete
                apiSearchRoute="/api/edu-providers/programs/college/search/"
                fieldLabel="Program major or concentration: *"
                id="profile-creation-education-college-program"
                searchingText="Searching..."
                noResultsText="No education provider programs found..."
                value={education[classProgramObject] ?? ""}
                onChange={(e, val) =>
                  handleChange(index, classProgramObject, val)
                }
                searchPlaceholder="Example: Computer Science"
                getOptionLabel={(option: GeneralProgramDTO) =>
                  option.title ?? ""
                }
              />
            </RequiredTooltip>
            <SelectOptionsWithLabel
              id="profile-creation-education-college-degree"
              className="w-full"
              options={(Object.values(CollegeDegreeType) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classDegreeType, e.target.value)
              }
              value={education[classDegreeType] as string}
            >
              Type of degree earned:
            </SelectOptionsWithLabel>
            {/*added for WJI data collection alignment (Please do not modify data).*/}
            <SelectOptionsWithLabel
              id="profile-creation-education-enrollment-status"
              className="w-full"
              options={(Object.values(ProgramEnrollmentStatus) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classEnrollmentStatus, e.target.value)
              }
              required
              value={education[classEnrollmentStatus] as string}
            >
              Enrollment status: *
            </SelectOptionsWithLabel>
            {/*end add for WJI data collection alignment*/}
          </div>
          <div className="profile-form-grid md:grid-cols-2">
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classStartDate}` &&
                !Boolean(education[classStartDate])
              }
              errorMessage="A starting date is required"
            >
              <DatePicker
                label={"Starting date *"}
                views={["month", "year"]}
                value={education[classStartDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(
                    index,
                    classStartDate,
                    val?.isValid() ? val : null,
                  )
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classEndDate}` &&
                !Boolean(education[classEndDate])
              }
              errorMessage="A completion date is required"
            >
              <DatePicker
                label={"Completion date *"}
                views={["month", "year"]}
                value={education[classEndDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(index, classEndDate, val?.isValid() ? val : null)
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
          </div>
          {/*  <Checkbox*/}
          {/*    id={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    name={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    checked={education[classIsCurrent]}*/}
          {/*    onChange={(e) =>*/}
          {/*      handleChange(index, classIsCurrent, e.target.checked)*/}
          {/*    }*/}
          {/*  />*/}
          {/*  Current*/}
          <div className="profile-form-grid">
            <InputTextWithLabel
              id={"profile-creation-education-college-gpa"}
              type="text"
              className="w-full"
              placeholder="Example: 4.0"
              onChange={(e) => handleChange(index, classGPA, e.target.value)}
              value={education[classGPA] ?? ""}
            >
              Grade Point Average (GPA):
            </InputTextWithLabel>
          </div>
        </div>
      )}
      {education[classEdLevel] !== EducationLevel.TrainingProgram ? (
        ""
      ) : (
        <div id="profile-creation-education-training-program-fields">
          <div className="profile-form-grid">
            <RequiredTooltip
              open={
                hasUnmetRequired ===
                  `${education.id}-${classEdProviderObject}` &&
                !Boolean(education[classEdProviderObject])
              }
              errorMessage="A training provider name is required"
            >
              <TextFieldWithAutocomplete
                apiSearchRoute="/api/edu-providers/search/"
                fieldLabel="Technical training provider: *"
                id="profile-creation-education-training-provider-name"
                searchingText="Searching..."
                noResultsText="No education providers found..."
                value={education[classEdProviderObject] ?? ""}
                onChange={(e, val) =>
                  handleChange(index, classEdProviderObject, val)
                }
                searchPlaceholder="Example: CompTIA"
                getOptionLabel={(option: EducationProviderDTO) =>
                  option.name ?? ""
                }
              />
            </RequiredTooltip>
            <TextFieldWithAutocomplete
              apiSearchRoute="/api/edu-providers/programs/training-programs/search/"
              fieldLabel="Program or training track subject:"
              id="profile-creation-education-training-provider-program-name"
              searchingText="Searching..."
              noResultsText="No education provider programs found..."
              value={education[classProgramObject] ?? ""}
              onChange={(e, val) =>
                handleChange(index, classProgramObject, val)
              }
              searchPlaceholder="Example: Cybersecurity"
              getOptionLabel={(option: GeneralProgramDTO) => option.title ?? ""}
            />
            {/*added for WJI data collection alignment (Please do not modify data).*/}
            <SelectOptionsWithLabel
              id="profile-creation-education-enrollment-status"
              className="w-full"
              options={(Object.values(ProgramEnrollmentStatus) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classEnrollmentStatus, e.target.value)
              }
              required
              value={education[classEnrollmentStatus] as string}
            >
              Enrollment status:
            </SelectOptionsWithLabel>
            {/*end add for WJI data collection alignment*/}
          </div>
          <div className="profile-form-grid md:grid-cols-2">
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classStartDate}` &&
                !Boolean(education[classStartDate])
              }
              errorMessage="A starting date is required"
            >
              <DatePicker
                label={"Starting date *"}
                views={["month", "year"]}
                value={education[classStartDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(
                    index,
                    classStartDate,
                    val?.isValid() ? val : null,
                  )
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classEndDate}` &&
                !Boolean(education[classEndDate])
              }
              errorMessage="A completion date is required"
            >
              <DatePicker
                label={"Completion date *"}
                views={["month", "year"]}
                value={education[classEndDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(index, classEndDate, val?.isValid() ? val : null)
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
          </div>
          {/*  <Checkbox*/}
          {/*    id={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    name={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    checked={education[classIsCurrent]}*/}
          {/*    onChange={(e) =>*/}
          {/*      handleChange(index, classIsCurrent, e.target.checked)*/}
          {/*    }*/}
          {/*  />*/}
          {/*  Current*/}
          <div className="profile-form-grid">
            <InputTextWithLabel
              id={"profile-creation-education-training-program-gpa"}
              type="text"
              className="w-full"
              placeholder="Example: 4.0"
              onChange={(e) => handleChange(index, classGPA, e.target.value)}
              value={education[classGPA] ?? ""}
            >
              Grade Point Average (GPA):
            </InputTextWithLabel>
          </div>
        </div>
      )}
      {education[classEdLevel] !== EducationLevel.PreApprenticeship ? (
        ""
      ) : (
        <div id="profile-creation-education-preapprenticeship-fields">
          <div className="profile-form-grid">
            <RequiredTooltip
              open={
                hasUnmetRequired ===
                  `${education.id}-${classEdProviderObject}` &&
                !Boolean(education[classEdProviderObject])
              }
              errorMessage="A pre-apprenticeship provider name is required"
            >
              <TextFieldWithAutocomplete
                apiSearchRoute="/api/edu-providers/search/"
                fieldLabel="Pre-apprenticeship provider: *"
                id="profile-creation-education-preapprenticeship-name"
                searchingText="Searching..."
                noResultsText="No education providers found..."
                value={education[classEdProviderObject] ?? ""}
                onChange={(e, val) =>
                  handleChange(index, classEdProviderObject, val)
                }
                searchPlaceholder="Example: Computing for All"
                getOptionLabel={(option: EducationProviderDTO) =>
                  option.name ?? ""
                }
              />
            </RequiredTooltip>
            <SelectOptionsWithLabel
              id="profile-creation-education-preapprenticeship-system"
              className="w-full"
              options={(Object.values(PreAEduSystem) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classPreAppEdSystem, e.target.value)
              }
              value={education[classPreAppEdSystem]?.toString() ?? ""}
            >
              Affiliated school system:
            </SelectOptionsWithLabel>
            <TextFieldWithAutocomplete
              apiSearchRoute="/api/edu-providers/programs/pre-apprenticeship/search/"
              fieldLabel="Program or training track subject:"
              id="profile-creation-education-preapprenticeship-program"
              searchingText="Searching..."
              noResultsText="No education provider programs found..."
              value={education[classProgramObject] ?? ""}
              onChange={(e, val) =>
                handleChange(index, classProgramObject, val)
              }
              searchPlaceholder="Example: Full stack web development"
              getOptionLabel={(option: GeneralProgramDTO) => option.title ?? ""}
            />
            {/*added for WJI data collection alignment (Please do not modify data).*/}
            <SelectOptionsWithLabel
              id="profile-creation-education-enrollment-status"
              className="w-full"
              options={(Object.values(ProgramEnrollmentStatus) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classEnrollmentStatus, e.target.value)
              }
              required
              value={education[classEnrollmentStatus] as string}
            >
              Enrollment status: *
            </SelectOptionsWithLabel>
            {/*end add for WJI data collection alignment*/}
          </div>
          <div className="profile-form-grid md:grid-cols-2">
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classStartDate}` &&
                !Boolean(education[classStartDate])
              }
              errorMessage="A starting date is required"
            >
              <DatePicker
                label={"Starting date *"}
                views={["month", "year"]}
                value={education[classStartDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(
                    index,
                    classStartDate,
                    val?.isValid() ? val : null,
                  )
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classEndDate}` &&
                !Boolean(education[classEndDate])
              }
              errorMessage="A completion date is required"
            >
              <DatePicker
                label={"Completion date *"}
                views={["month", "year"]}
                value={education[classEndDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(index, classEndDate, val?.isValid() ? val : null)
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
          </div>
          {/*  <Checkbox*/}
          {/*    id={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    name={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    checked={education[classIsCurrent]}*/}
          {/*    onChange={(e) =>*/}
          {/*      handleChange(index, classIsCurrent, e.target.checked)*/}
          {/*    }*/}
          {/*  />*/}
          {/*  Current*/}
          <div className="profile-form-grid">
            <InputTextWithLabel
              id={"profile-creation-education-preapprenticeship-gpa"}
              type="text"
              className="w-full"
              placeholder="Example: 4.0"
              onChange={(e) => handleChange(index, classGPA, e.target.value)}
              value={education[classGPA] ?? ""}
            >
              Grade Point Average (GPA):
            </InputTextWithLabel>
          </div>
        </div>
      )}
      {education[classEdLevel] !== EducationLevel.Other ? (
        ""
      ) : (
        <div id="profile-creation-education-other-fields">
          <div className="profile-form-grid">
            <RequiredTooltip
              open={
                hasUnmetRequired ===
                  `${education.id}-${classEdProviderObject}` &&
                !Boolean(education[classEdProviderObject])
              }
              errorMessage="An education provider name is required"
            >
              <TextFieldWithAutocomplete
                apiSearchRoute="/api/edu-providers/search/"
                fieldLabel="Name of education provider: *"
                id="profile-creation-education-other-provider-name"
                searchingText="Searching..."
                noResultsText="No education providers found..."
                value={education[classEdProviderObject] ?? ""}
                onChange={(e, val) =>
                  handleChange(index, classEdProviderObject, val)
                }
                searchPlaceholder="Example: edX"
                getOptionLabel={(option: EducationProviderDTO) =>
                  option.name ?? ""
                }
              />
            </RequiredTooltip>
            <TextFieldWithAutocomplete
              apiSearchRoute="/api/edu-providers/programs/other/search/"
              fieldLabel="Program or training track subject:"
              id="profile-creation-education-other-provider-program-name"
              searchingText="Searching..."
              noResultsText="No education provider programs found..."
              value={education[classProgramObject] ?? ""}
              onChange={(e, val) =>
                handleChange(index, classProgramObject, val)
              }
              searchPlaceholder="Example: Computer Science"
              getOptionLabel={(option: GeneralProgramDTO) => option.title ?? ""}
            />
            {/*added for WJI data collection alignment (Please do not modify data).*/}
            <SelectOptionsWithLabel
              id="profile-creation-education-enrollment-status"
              className="w-full"
              options={(Object.values(ProgramEnrollmentStatus) as string[]).map(
                (value) => ({ label: value, value }),
              )}
              placeholder="Please select"
              onChange={(e) =>
                handleChange(index, classEnrollmentStatus, e.target.value)
              }
              required
              value={education[classEnrollmentStatus] as string}
            >
              Enrollment status: *
            </SelectOptionsWithLabel>
            {/*end add for WJI data collection alignment*/}
          </div>
          <div className="profile-form-grid md:grid-cols-2">
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classStartDate}` &&
                !Boolean(education[classStartDate])
              }
              errorMessage="A starting date is required"
            >
              <DatePicker
                label={"Starting date *"}
                views={["month", "year"]}
                value={education[classStartDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(
                    index,
                    classStartDate,
                    val?.isValid() ? val : null,
                  )
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
            <RequiredTooltip
              open={
                hasUnmetRequired === `${education.id}-${classEndDate}` &&
                !Boolean(education[classEndDate])
              }
              errorMessage="A completion date is required"
            >
              <DatePicker
                label={"Completion date *"}
                views={["month", "year"]}
                value={education[classEndDate] || null}
                onChange={(val: Dayjs | null) =>
                  handleChange(index, classEndDate, val?.isValid() ? val : null)
                }
                slotProps={{ textField: { fullWidth: true } }}
              />
            </RequiredTooltip>
          </div>
          {/*  <Checkbox*/}
          {/*    id={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    name={classNamePrefix + education.id + '-' + classIsCurrent}*/}
          {/*    checked={education[classIsCurrent]}*/}
          {/*    onChange={(e) =>*/}
          {/*      handleChange(index, classIsCurrent, e.target.checked)*/}
          {/*    }*/}
          {/*  />*/}
          {/*  Current*/}
          <div className="profile-form-grid">
            <InputTextWithLabel
              id={"profile-creation-education-other-gpa"}
              type="text"
              className="w-full"
              placeholder="Example: 4.0"
              onChange={(e) => handleChange(index, classGPA, e.target.value)}
              value={education[classGPA] ?? ""}
            >
              Grade Point Average (GPA):
            </InputTextWithLabel>
          </div>
        </div>
      )}
    </fieldset>
  ));
});
