import React, { memo, useCallback } from "react";
import PillButton from "@/app/ui/components/PillButton";
import { Checkbox } from "@mui/material";
import InputTextWithLabel from "@/app/ui/components/InputTextWithLabel";
import TextareaWithLabel from "@/app/ui/components/TextareaWithLabel";
import { v4 as uuidv4 } from "uuid";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Dayjs } from "dayjs";
import SelectAutoload from "@/app/ui/components/mui/SelectAutoload";
import { IndustrySectorDropdownDTO } from "@/data/dtos/IndustrySectorDropdownDTO";
import { TechnologyAreaDropdownDTO } from "@/data/dtos/TechnologyAreaDropdownDTO";
import RequiredTooltip from "@/app/ui/components/mui/RequiredTooltip";
import { Close } from "@mui/icons-material";

const classNamePrefix = "profile-creation-work-experience-group-";
const classCompany = "company";
const classCompanyIndustry = "sectorObject";
const classCompanyTechArea = "techAreaObject";
const classTitle = "jobTitle";
const classStarts = "startDate";
const classEnds = "endDate";
const classCurrent = "isCurrentJob";
const classExperience = "responsibilities";

export interface WorkExperienceData {
  workId: string;
  [classCompany]: string;
  [classCompanyIndustry]: IndustrySectorDropdownDTO;
  [classCompanyTechArea]: TechnologyAreaDropdownDTO;
  [classTitle]: string;
  [classStarts]: Dayjs | null;
  [classEnds]: Dayjs | null;
  [classCurrent]: boolean;
  [classExperience]: string;
}

export function defaultWorkExperienceData(): WorkExperienceData {
  return {
    workId: uuidv4(),
    [classCompany]: "",
    [classCompanyIndustry]: { industry_sector_id: "", sector_title: "" },
    [classCompanyTechArea]: { id: "", title: "" },
    [classTitle]: "",
    [classStarts]: null,
    [classEnds]: null,
    [classCurrent]: false,
    [classExperience]: "",
  };
}

interface Props {
  data: WorkExperienceData[];
  hasUnmetRequired: string;
  onRemove: (uid: string) => void;
  onUpdate: (key: string, value: any) => void;
}

export default memo(function WorkExperiences({
  data,
  hasUnmetRequired,
  onRemove,
  onUpdate,
}: Props) {
  const handleChange = useCallback(
    <K extends keyof WorkExperienceData>(index: number, key: K, value: any) => {
      const changedWorkExperiences: WorkExperienceData[] = [...data];
      const updatedWorkExperience = changedWorkExperiences[index];
      updatedWorkExperience[key] = value;
      onUpdate("workExperiences", changedWorkExperiences);
    },
    [data, onUpdate],
  );

  return data.map((workExperience, index) => (
    <fieldset key={classNamePrefix + workExperience.workId + "-key"}>
      <legend className="flex w-full justify-between">
        <h3>Work Experience {index + 1}</h3>
        <PillButton
          onClick={() => onRemove(workExperience.workId)}
          variant="outlined"
        >
          <Close className="h-5 w-5" />
        </PillButton>
      </legend>
      <div className="profile-form-grid">
        <InputTextWithLabel
          id={classNamePrefix + workExperience.workId + "-" + classCompany}
          className="w-full"
          placeholder="Example: Microsoft"
          onChange={(e) => handleChange(index, classCompany, e.target.value)}
          required
          value={workExperience[classCompany]}
        >
          Company Name:
        </InputTextWithLabel>
        <SelectAutoload
          id={
            classNamePrefix + workExperience.workId + "-" + classCompanyIndustry
          }
          apiAutoloadRoute="/api/employers/industry-sectors"
          label="Industry Sector: *"
          getOptionLabel={(option: IndustrySectorDropdownDTO) =>
            option.sector_title
          }
          getOptionId={(option: IndustrySectorDropdownDTO) =>
            option.industry_sector_id
          }
          getOptionFromId={(options: IndustrySectorDropdownDTO[], id: string) =>
            options.find((item) => item.industry_sector_id === id) || null
          }
          placeholder="Please select"
          onChange={(val) => handleChange(index, classCompanyIndustry, val)}
          value={workExperience[classCompanyIndustry]}
          loadingText="Retrieving industry sectors..."
        />
        <SelectAutoload
          id={
            classNamePrefix + workExperience.workId + "-" + classCompanyTechArea
          }
          apiAutoloadRoute="/api/employers/technology-areas"
          label="Job Role or Department: *"
          getOptionLabel={(option: TechnologyAreaDropdownDTO) => option.title}
          getOptionId={(option: TechnologyAreaDropdownDTO) => option.id}
          getOptionFromId={(options: TechnologyAreaDropdownDTO[], id: string) =>
            options.find((item) => item.id === id) || null
          }
          placeholder="Please select"
          onChange={(val) => handleChange(index, classCompanyTechArea, val)}
          value={workExperience[classCompanyTechArea]}
          loadingText="Retrieving technology areas..."
        />
        <InputTextWithLabel
          id={classNamePrefix + workExperience.workId + "-" + classTitle}
          className="w-full"
          placeholder="Example: Frontend Developer"
          onChange={(e) => handleChange(index, classTitle, e.target.value)}
          required
          value={workExperience[classTitle]}
        >
          Your Job Title:
        </InputTextWithLabel>
      </div>
      <div className="profile-form-grid md:grid-cols-2">
        <RequiredTooltip
          open={
            hasUnmetRequired === `${workExperience.workId}-${classStarts}` &&
            !Boolean(workExperience[classStarts])
          }
          errorMessage="A start date is required"
        >
          <DatePicker
            label={"Start Date *"}
            views={["month", "year"]}
            value={
              workExperience[classStarts]?.isValid()
                ? workExperience[classStarts]
                : null
            }
            onChange={(val) =>
              handleChange(index, classStarts, val?.isValid() ? val : null)
            }
            slotProps={{ textField: { fullWidth: true } }}
          />
        </RequiredTooltip>
        <RequiredTooltip
          open={
            hasUnmetRequired === `${workExperience.workId}-${classEnds}` &&
            !Boolean(workExperience[classEnds]) &&
            !Boolean(workExperience[classCurrent])
          }
          errorMessage="An end date is required if you're no longer working here"
        >
          <DatePicker
            label={"End Date"}
            views={["month", "year"]}
            value={
              workExperience[classEnds]?.isValid()
                ? workExperience[classEnds]
                : null
            }
            onChange={(val) =>
              handleChange(index, classEnds, val?.isValid() ? val : null)
            }
            slotProps={{ textField: { fullWidth: true } }}
          />
        </RequiredTooltip>
      </div>
      <Checkbox
        id={classNamePrefix + workExperience.workId + "-" + classCurrent}
        name={classNamePrefix + workExperience.workId + "-" + classCurrent}
        checked={workExperience[classCurrent]}
        onChange={(e) => handleChange(index, classCurrent, e.target.checked)}
      />
      Currently Employed in this Position
      <div className="profile-form-grid">
        <TextareaWithLabel
          id={classNamePrefix + workExperience.workId + "-" + classExperience}
          placeholder="Example: Write CSS for design changes"
          onChange={(e: { target: { value: any } }) =>
            handleChange(index, classExperience, e.target.value)
          }
          required
          value={workExperience[classExperience]}
        >
          Job Responsibilities: *
        </TextareaWithLabel>
      </div>
    </fieldset>
  ));
});
