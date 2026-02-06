"use client";

import {
  Stepper,
  FormControl,
  FormLabel,
  TextField,
  Step,
  StepLabel,
  Typography,
  Select,
  FormHelperText,
  Stack,
  Grid,
  Box,
  Link,
  MenuItem,
  RadioGroup,
  FormControlLabel,
  Radio,
  FormGroup,
  Checkbox,
  Autocomplete,
  Chip,
  createFilterOptions,
} from "@mui/material";
import { DatePicker, LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";
import { useEffect, useState } from "react";
import PillButton from "../PillButton";
import {
  ArrowCircleRightOutlined,
  FileUploadOutlined,
} from "@mui/icons-material";
import SingleSelectFilterAutoload from "../mui/SingleSelectFilterAutoload";
import { IndustrySectorDropdownDTO } from "@/data/dtos/IndustrySectorDropdownDTO";
import { EarnLearnType, EmploymentType } from "@/app/lib/admin/jobTracking";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import TagsWithAutocomplete from "../mui/TagsWithAutocomplete";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import { TechnologyAreaDropdownDTO } from "@/data/dtos/TechnologyAreaDropdownDTO";
import dayjs, { Dayjs } from "dayjs";
import { HighestCompletedEducationLevel } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import QuillEditor from "./QuillEditor";
import TextFieldWithAutocomplete from "../mui/TextFieldWithAutocomplete";

function getCompensationType(salary_range: string) {
  const lowerCaseSalary = salary_range.toLowerCase();
  if (lowerCaseSalary.includes("year") || lowerCaseSalary.includes("yr")) {
    return "annual";
  }
  if (lowerCaseSalary.includes("hour") || lowerCaseSalary.includes("hr")) {
    return "hourly";
  }
  return "";
}

const steps = [
  "Job Information",
  "Employment Information",
  "Qualifications",
  "Publish",
];

export default function NewJobForm({
  company_id,
  job_posting,
  isAdminOrCaseManager,
  onJobUpdated,
}: {
  company_id: string | null;
  job_posting?: JobPostCreationDTO;
  isAdminOrCaseManager?: boolean;
  onJobUpdated?: (job: JobPostCreationDTO) => void;
}) {
  const [activeStep, setActiveStep] = useState(0);
  const [isParsingSkills, setIsParsingSkills] = useState(false);

  // Step 0: Job Information state
  const [jobTitle, setJobTitle] = useState("");
  const [jobUrl, setJobUrl] = useState("");
  const [jobDescription, setJobDescription] = useState("");
  const [industry, setIndustry] = useState("");
  const [techArea, setTechArea] = useState("");
  const [occupationCode, setOccupationCode] = useState("");
  const [applicationDeadline, setApplicationDeadline] = useState<Dayjs | null>(
    null,
  );

  // Step 1: Employment Information state
  const [employmentType, setEmploymentType] = useState("");
  const [earnAndLearnType, setEarnAndLearnType] = useState<string | null>(null);
  const [careerServicesOffered, setCareerServicesOffered] = useState<
    boolean | null
  >(true);
  const [paidPosition, setPaidPosition] = useState(false);
  const [internship, setInternship] = useState(false);
  const [apprenticeship, setApprenticeship] = useState(false);
  const [location, setLocation] = useState("");
  const [relocation, setRelocation] = useState(false);
  const [visaSponsor, setVisaSponsor] = useState(false);
  const [employmentDuration, setEmploymentDuration] = useState("");
  const [startDate, setStartDate] = useState<Dayjs | null>(null);
  const [endDate, setEndDate] = useState<Dayjs | null>(null);
  const [employmentIsPermanent, setEmploymentIsPermanent] =
    useState("permanent");
  const [workEnvironment, setWorkEnvironment] = useState("");
  const [startingPayRange, setStartingPayRange] = useState("");
  const [endingPayRange, setEndingPayRange] = useState("");
  const [compensationType, setCompensationType] = useState("");

  // Step 2: Qualifications state
  const [requiredSkills, setRequiredSkills] = useState<SkillDTO[]>([]);
  const [trainingRequirements, setTrainingRequirements] = useState("");
  const [requiredCertifications, setRequiredCertifications] = useState("");
  const [educationLevel, setEducationLevel] =
    useState<HighestCompletedEducationLevel>(
      HighestCompletedEducationLevel.NoFormalEducation,
    );

  useEffect(() => {
    if (job_posting) {
      // Step 0: Job Information state
      setJobTitle(job_posting.job_title);
      setJobUrl(job_posting.job_post_url || "");
      setJobDescription(job_posting.job_description);
      setIndustry(job_posting.sector_id || "");
      setTechArea(job_posting.techArea?.id || job_posting.tech_area_id || "");
      setOccupationCode(job_posting.occupation_code || "");
      setApplicationDeadline(
        job_posting.unpublish_date ? dayjs(job_posting.unpublish_date) : null,
      );

      // Step 1: Employment Information state
      setEmploymentType(job_posting.employment_type || "");
      setEarnAndLearnType(job_posting.earn_and_learn_type || null);
      setCareerServicesOffered(job_posting.career_services_offered || true);
      setPaidPosition(job_posting.is_paid || false);
      setInternship(job_posting.is_internship || false);
      setApprenticeship(job_posting.is_apprenticeship || false);
      setLocation(job_posting.zip || "");
      setRelocation(job_posting.relocation_services_available || false);
      setVisaSponsor(job_posting.offer_visa_sponsorship || false);
      setEmploymentDuration(job_posting.employment_duration || "");
      setStartDate(
        job_posting.start_date ? dayjs(job_posting.start_date) : null,
      );
      setEndDate(job_posting.end_date ? dayjs(job_posting.end_date) : null);
      setEmploymentIsPermanent(
        job_posting.employment_duration &&
          job_posting.employment_duration.length > 0
          ? "temporary"
          : job_posting.end_date
            ? "temporary"
            : "permanent",
      );
      setWorkEnvironment(job_posting.location);

      // Parse salary range
      if (job_posting.salary_range) {
        console.log(job_posting.salary_range);
        const salaryWithoutCommas = job_posting.salary_range.replace(/,/g, "");
        const regex = /(\d+)/g;
        const numbers = salaryWithoutCommas.match(regex);

        if (numbers) {
          setStartingPayRange(numbers[0] || "");
          setEndingPayRange(numbers.length > 1 ? numbers[1] : "");
        }
      }
      setCompensationType(getCompensationType(job_posting.salary_range));

      // Step 2: Qualifications state
      if (job_posting.skills) {
        setRequiredSkills(job_posting.skills);
      }
      setTrainingRequirements(job_posting.trainingRequirements || "");
      setRequiredCertifications(job_posting.requiredCertifications || "");
      setEducationLevel(
        (job_posting.minimumEducationLevel as HighestCompletedEducationLevel) ||
          HighestCompletedEducationLevel.NoFormalEducation,
      );
    }
  }, [job_posting]);

  const isStepValid = () => {
    if (activeStep === 0) {
      return (
        jobTitle.trim() !== "" &&
        jobUrl.includes("https://") &&
        jobDescription.trim() !== "" &&
        occupationCode.trim() !== "" &&
        applicationDeadline
      );
    }
    if (activeStep === 1) {
      const basicValid = employmentType.trim() !== "" && location.trim() !== "";
      const earnLearnValid =
        employmentType === EmploymentType.EarnAndLearn
          ? earnAndLearnType
          : true;
      const durationValid =
        employmentIsPermanent === "permanent" ||
        (employmentIsPermanent === "temporary" &&
          employmentDuration.trim() !== "");
      const datesValid =
        employmentIsPermanent === "permanent" ||
        (employmentIsPermanent === "temporary" && startDate?.isBefore(endDate));
      const compensationValid =
        !paidPosition ||
        (startingPayRange.trim() !== "" &&
          compensationType.trim() !== "" &&
          (endingPayRange.trim() === "" ||
            Number(endingPayRange) > Number(startingPayRange)));
      return (
        basicValid &&
        earnLearnValid &&
        (durationValid || datesValid) &&
        compensationValid
      );
    }
    return true;
  };

  const handleSubmit = async () => {
    const jobListingData: JobPostCreationDTO = {
      company_id: company_id,
      job_title: jobTitle,
      job_post_url: jobUrl,
      job_description: jobDescription,
      sector_id: industry,
      tech_area_id: techArea,
      occupation_code: occupationCode,
      unpublish_date: applicationDeadline?.toDate() ?? null,
      employment_type: employmentType,
      earn_and_learn_type:
        employmentType === EmploymentType.EarnAndLearn
          ? earnAndLearnType
          : null,
      career_services_offered: careerServicesOffered,
      location: workEnvironment,
      zip: location,
      is_paid: paidPosition,
      salary_range: paidPosition
        ? "$" +
          Number(startingPayRange).toLocaleString() +
          (endingPayRange
            ? " - $" + Number(endingPayRange).toLocaleString()
            : "") +
          (compensationType === "hourly" ? " / hr" : " / year")
        : "",
      skillIds: requiredSkills.map((skill) => skill.skill_id),
      is_internship: internship,
      is_apprenticeship: apprenticeship,
      relocation_services_available: relocation,
      offer_visa_sponsorship: visaSponsor,
      techArea: null,
      jobApplications: [],
      publish_date: null,
      assessment_url: null,
      employment_duration:
        employmentIsPermanent === "temporary" ? employmentDuration : null,
      start_date: startDate?.toDate() ?? null,
      end_date:
        employmentIsPermanent === "temporary"
          ? (endDate?.toDate() ?? null)
          : null,
      trainingRequirements: trainingRequirements,
      requiredCertifications: requiredCertifications,
      minimumEducationLevel: educationLevel,
    };
    const apiEndpoint = job_posting?.job_posting_id
      ? "/api/joblistings/update"
      : "/api/joblistings/add";
    if (job_posting?.job_posting_id) {
      jobListingData.job_posting_id = job_posting.job_posting_id;
    }

    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(jobListingData),
      });
      if (!response.ok) {
        const errorData = await response.json();
        console.error(
          `Failed to ${job_posting ? "update" : "create"} job listing:`,
          errorData,
        );
        alert(`Error: ${errorData.message || "Could not save job listing."}`);
        return;
      }

      const savedJob = await response.json();
      console.log("Job saved successfully:", savedJob);
      if (onJobUpdated) {
        onJobUpdated(savedJob);
      }
    } catch (error) {
      console.error(
        `Error ${job_posting ? "updating" : "creating"} job listing:`,
        error,
      );
      alert("An unexpected error occurred. Please try again.");
    }
  };

  async function handleNext() {
    if (isStepValid()) {
      const shouldParseSkills =
        activeStep === 0 && requiredSkills.length === 0 && !isParsingSkills;
      const descriptionToParse = shouldParseSkills ? jobDescription.trim() : "";
      setActiveStep((prev) => prev + 1);
      if (shouldParseSkills && descriptionToParse) {
        parseSkillsInBackground(descriptionToParse);
      }
    }
  }

  function handleBack() {
    setActiveStep((prev) => prev - 1);
  }

  async function parseSkillsInBackground(description: string) {
    if (isParsingSkills || requiredSkills.length > 0) {
      return;
    }
    if (!description) {
      return;
    }

    setIsParsingSkills(true);
    try {
      const response = await fetch("/api/skills/parse-text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: description }),
      });

      if (response.ok) {
        const parsedSkills: SkillDTO[] = await response.json();
        const topSkills = parsedSkills.slice(0, 10);
        setRequiredSkills((currentSkills) => {
          if (currentSkills.length === 0) {
            console.log("Skills parsed and state updated:", topSkills);
            return topSkills;
          }
          return currentSkills;
        });
      } else {
        console.error(
          "Failed to parse skills from description (background):",
          response.status,
          await response.text(),
        );
      }
    } catch (error) {
      console.error("Error calling skill parsing API (background):", error);
    } finally {
      setIsParsingSkills(false);
    }
  }

  const getChipsArray = (value: string) =>
    value
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s.length > 0);

  const filter = createFilterOptions<string>();

  return (
    <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="en">
      <Stepper
        activeStep={activeStep}
        sx={{ display: { xs: "none", sm: "flex" } }}
      >
        {steps.map((label) => {
          const stepProps: { completed?: boolean } = {};
          const labelProps: {
            optional?: React.ReactNode;
          } = {};
          return (
            <Step key={label} {...stepProps}>
              <StepLabel {...labelProps}>
                {label == "Publish"
                  ? job_posting
                    ? "Update"
                    : "Publish"
                  : label}
              </StepLabel>
            </Step>
          );
        })}
      </Stepper>
      <Typography
        sx={{ justifySelf: "center", display: { xs: "flex", sm: "none" } }}
      >
        {activeStep + 1} / {steps.length}
      </Typography>
      <Typography variant="h5" sx={{ my: 2 }}>
        {steps[activeStep]}
      </Typography>
      <Stack>
        {activeStep === 0 && (
          <Stack spacing={3}>
            <FormControl fullWidth>
              <FormLabel required>Job Title</FormLabel>
              <TextField
                required
                value={jobTitle}
                onChange={(e) => setJobTitle(e.target.value)}
                helperText="Enter a clear and concise job title (e.g., Senior Software Engineer, Marketing Manager)"
              />
            </FormControl>

            <FormControl fullWidth>
              <FormLabel required>Job Application Form URL</FormLabel>
              <TextField
                required
                value={jobUrl}
                onChange={(e) => setJobUrl(e.target.value)}
                placeholder="https://example.org"
                helperText="Enter a URL to the job post, if applicable"
              />
            </FormControl>

            <FormControl fullWidth>
              <FormLabel required>Job Description</FormLabel>
              <QuillEditor
                html={jobDescription}
                onChangeAction={setJobDescription}
              />
            </FormControl>

            <FormControl fullWidth>
              <FormLabel required>Industry</FormLabel>
              <SingleSelectFilterAutoload<IndustrySectorDropdownDTO>
                id="newjobform-Industry"
                label=""
                apiAutoloadRoute="/api/employers/industry-sectors"
                value={industry}
                onChange={(e) => setIndustry(e.target.value)}
                getOptionLabel={(option: IndustrySectorDropdownDTO) =>
                  option.sector_title
                }
                getOptionValue={(option: IndustrySectorDropdownDTO) =>
                  option.industry_sector_id
                }
              />
              <FormHelperText>
                Select the industry that best fits this role
              </FormHelperText>
            </FormControl>

            <FormControl fullWidth>
              <FormLabel required>Tech Area</FormLabel>
              <SingleSelectFilterAutoload<TechnologyAreaDropdownDTO>
                id="newjobform-tech-area"
                label=""
                apiAutoloadRoute="/api/employers/technology-areas"
                value={techArea}
                onChange={(e) => setTechArea(e.target.value)}
                getOptionLabel={(option: TechnologyAreaDropdownDTO) =>
                  option.title
                }
                getOptionValue={(option: TechnologyAreaDropdownDTO) =>
                  option.id
                }
              />
              <FormHelperText>
                Select the technology area that best fits this role
              </FormHelperText>
            </FormControl>

            <FormControl fullWidth>
              <FormLabel required>Occupation Code (SOCC)</FormLabel>
              <TextFieldWithAutocomplete<{
                id: string;
                title: string;
                description: string | null;
              }>
                apiSearchRoute="/api/socc/search/"
                fieldLabel=""
                searchingText="Searching..."
                noResultsText="No socc code found..."
                value={occupationCode ?? ""}
                onChange={(
                  _event,
                  value:
                    | string
                    | { id: string; title: string; description: string | null }
                    | null,
                ) => {
                  if (value && typeof value === "object" && "id" in value) {
                    setOccupationCode(value.id);
                  } else {
                    setOccupationCode("");
                  }
                }}
                searchPlaceholder=""
                allowNewOption={false}
                getOptionLabel={(option) => `${option?.id} - ${option.title}`}
              />
              <FormHelperText>Select an occupation code</FormHelperText>
            </FormControl>

            <FormControl fullWidth>
              <FormLabel required>Application Deadline</FormLabel>
              <DatePicker
                disablePast
                value={applicationDeadline}
                onChange={(newValue) => setApplicationDeadline(newValue)}
              />
              <FormHelperText>
                Select the deadline for applications
              </FormHelperText>
            </FormControl>
          </Stack>
        )}
        {activeStep === 1 && (
          <Stack spacing={3}>
            <FormControl fullWidth>
              <Grid container direction="row" spacing={2}>
                <div>
                  <FormLabel required>Employment Type</FormLabel>
                  <Select
                    fullWidth
                    required
                    value={employmentType}
                    onChange={(e) => setEmploymentType(e.target.value)}
                  >
                    {Object.values(EmploymentType).map((code) => (
                      <MenuItem key={code + 1} value={code}>
                        {code}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>
                    Select the employment type for this role
                  </FormHelperText>
                </div>
                <FormGroup row>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={paidPosition}
                        onChange={(e) => setPaidPosition(e.target.checked)}
                        name="paid-position"
                      />
                    }
                    label="Paid Position"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={internship}
                        onChange={(e) => setInternship(e.target.checked)}
                        name="internship"
                      />
                    }
                    label="Internship"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={apprenticeship}
                        onChange={(e) => setApprenticeship(e.target.checked)}
                        name="apprenticeship"
                      />
                    }
                    label="Apprenticeship"
                  />
                </FormGroup>
              </Grid>
            </FormControl>

            <FormControl fullWidth>
              <Grid container direction="row" spacing={2}>
                <div>
                  <FormLabel
                    required={employmentType === EmploymentType.EarnAndLearn}
                  >
                    Earn and Learn Type
                  </FormLabel>
                  <Select
                    fullWidth
                    disabled={employmentType !== EmploymentType.EarnAndLearn}
                    required
                    value={earnAndLearnType ?? ""}
                    onChange={(e) => setEarnAndLearnType(e.target.value)}
                  >
                    {Object.values(EarnLearnType).map((code) => (
                      <MenuItem key={code + 1} value={code}>
                        {code}
                      </MenuItem>
                    ))}
                  </Select>
                  <FormHelperText>
                    Select the earn and learn type for this role
                  </FormHelperText>
                </div>
                {isAdminOrCaseManager && (
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={careerServicesOffered ?? true}
                        onChange={(e) =>
                          setCareerServicesOffered(e.target.checked)
                        }
                        name="paid-position"
                      />
                    }
                    label="Employer Partner Job"
                  />
                )}
              </Grid>
            </FormControl>

            <FormControl fullWidth>
              <FormLabel>Employment Duration</FormLabel>
              <Grid container direction="row" spacing={2}>
                <TextField
                  required
                  disabled={employmentIsPermanent === "permanent"}
                  placeholder="3 Months"
                  value={employmentDuration}
                  onChange={(e) => setEmploymentDuration(e.target.value)}
                  helperText="Expected duration of employment"
                />
                <RadioGroup
                  value={employmentIsPermanent}
                  onChange={(e) => setEmploymentIsPermanent(e.target.value)}
                  row
                >
                  <FormControlLabel
                    value="permanent"
                    control={<Radio />}
                    label="Permanent"
                  />
                  <FormControlLabel
                    value="temporary"
                    control={<Radio />}
                    label="Temporary"
                  />
                </RadioGroup>
              </Grid>
            </FormControl>

            <FormControl>
              <FormLabel>Start Date</FormLabel>
              <DatePicker
                disablePast
                value={startDate}
                onChange={(newValue) => setStartDate(newValue)}
              />
              <FormHelperText>Select when the job would start</FormHelperText>
            </FormControl>

            <FormControl>
              <FormLabel>End Date</FormLabel>
              <DatePicker
                disablePast
                disabled={employmentIsPermanent === "permanent"}
                value={endDate}
                onChange={(newValue) => setEndDate(newValue)}
              />
              <FormHelperText>Select when the job would end</FormHelperText>
            </FormControl>

            <FormControl fullWidth>
              <Grid container direction="row" spacing={2}>
                <div>
                  <FormLabel required>ZIP Code</FormLabel>
                  <TextField
                    fullWidth
                    required
                    value={location}
                    onChange={(e) => {
                      const numericValue = e.target.value.replace(
                        /[^0-9]/g,
                        "",
                      );
                      setLocation(numericValue);
                    }}
                    slotProps={{
                      htmlInput: {
                        maxLength: 5,
                        inputMode: "numeric",
                      },
                    }}
                  ></TextField>
                  <FormHelperText>
                    Enter the zip code (location) of the role
                  </FormHelperText>
                </div>
                <FormGroup row>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={relocation}
                        onChange={(e) => setRelocation(e.target.checked)}
                        name="relocation"
                      />
                    }
                    label="Relocation Assistance"
                  />
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={visaSponsor}
                        onChange={(e) => setVisaSponsor(e.target.checked)}
                        name="visaSponsor"
                      />
                    }
                    label="H1B Visa Sponsorship"
                  />
                </FormGroup>
              </Grid>
            </FormControl>
            <div>
              <FormControl>
                <FormLabel>Work Environment</FormLabel>
                <Select
                  required
                  value={workEnvironment}
                  onChange={(e) => setWorkEnvironment(e.target.value)}
                >
                  <MenuItem value="">Any</MenuItem>
                  <MenuItem value="remote">Remote</MenuItem>
                  <MenuItem value="hybrid">Hybrid</MenuItem>
                  <MenuItem value="on-site">On-Site</MenuItem>
                </Select>
                <FormHelperText>Enter the work environment</FormHelperText>
              </FormControl>
            </div>
            <FormControl fullWidth disabled={!paidPosition}>
              <FormLabel required>Compensation</FormLabel>
              <Grid container direction="row" spacing={2}>
                <TextField
                  required
                  disabled={!paidPosition}
                  placeholder="40000"
                  value={startingPayRange}
                  onChange={(e) => {
                    const numericValue = e.target.value.replace(/[^0-9]/g, "");
                    setStartingPayRange(numericValue);
                  }}
                  slotProps={{
                    htmlInput: {
                      inputMode: "numeric",
                    },
                  }}
                  helperText="Start range"
                />
                <TextField
                  required
                  disabled={!paidPosition}
                  placeholder="80000"
                  value={endingPayRange}
                  onChange={(e) => {
                    const numericValue = e.target.value.replace(/[^0-9]/g, "");
                    setEndingPayRange(numericValue);
                  }}
                  slotProps={{
                    htmlInput: {
                      inputMode: "numeric",
                    },
                  }}
                  helperText="End range"
                />
                <RadioGroup
                  value={compensationType}
                  onChange={(e) => setCompensationType(e.target.value)}
                  row
                >
                  <FormControlLabel
                    value="hourly"
                    control={<Radio />}
                    label="Hourly"
                  />
                  <FormControlLabel
                    value="annual"
                    control={<Radio />}
                    label="Annual"
                  />
                </RadioGroup>
              </Grid>
            </FormControl>
          </Stack>
        )}
        {activeStep === 2 && (
          <Stack spacing={3}>
            <FormControl fullWidth>
              <FormLabel>Top 10 required skills</FormLabel>
              <TagsWithAutocomplete
                apiSearchRoute="/api/skills/search/"
                fieldLabel=""
                id="employer-jobpost-skills"
                maxTags={10}
                searchingText="Searching..."
                noResultsText="No skills found..."
                onChange={(event: any, val: any) => {
                  if (
                    val.every(
                      (skill: string | SkillDTO) => typeof skill !== "string",
                    )
                  ) {
                    setRequiredSkills(val as SkillDTO[]);
                  }
                }}
                value={requiredSkills}
                searchPlaceholder="Skill (ex: Java)"
                getTagLabel={(option: SkillDTO) => option.skill_name}
                getTagLink={(option: SkillDTO) => option.skill_info_url}
              />
              <FormHelperText>
                Enter up to ten required skills needed for this role. Start
                typing to see suggestions and select multiple skill
              </FormHelperText>
            </FormControl>

            <FormControl fullWidth>
              <FormLabel>Training Requirements</FormLabel>
              <Autocomplete
                multiple
                freeSolo
                value={getChipsArray(trainingRequirements)}
                onChange={(event, newValue) => {
                  const processedValues = newValue.map((item) => {
                    if (typeof item === "string") {
                      if (item.startsWith('Add "')) {
                        return item.substring(5, item.length - 1);
                      }
                      return item;
                    }
                    return item;
                  });
                  setTrainingRequirements(processedValues.join(", "));
                }}
                filterOptions={(options, params) => {
                  const filtered = filter(options, params);
                  if (params.inputValue !== "") {
                    filtered.push(`Add "${params.inputValue}"`);
                  }
                  return filtered;
                }}
                selectOnFocus
                clearOnBlur
                handleHomeEndKeys
                options={[]}
                renderTags={(value: string[], getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      {...getTagProps({ index })}
                      key={index}
                    />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    placeholder="Enter training requirement"
                    helperText="Type and press Enter to add training requirement"
                  />
                )}
              />
            </FormControl>
            <FormControl fullWidth>
              <FormLabel>Required Certifications</FormLabel>
              <Autocomplete
                multiple
                freeSolo
                value={getChipsArray(requiredCertifications)}
                onChange={(event, newValue) => {
                  const processedValues = newValue.map((item) => {
                    if (typeof item === "string") {
                      if (item.startsWith('Add "')) {
                        return item.substring(5, item.length - 1);
                      }
                      return item;
                    }
                    return item;
                  });
                  setRequiredCertifications(processedValues.join(", "));
                }}
                filterOptions={(options, params) => {
                  const filtered = filter(options, params);
                  if (params.inputValue !== "") {
                    filtered.push(`Add "${params.inputValue}"`);
                  }
                  return filtered;
                }}
                selectOnFocus
                clearOnBlur
                handleHomeEndKeys
                options={[]}
                renderTags={(value: string[], getTagProps) =>
                  value.map((option, index) => (
                    <Chip
                      label={option}
                      {...getTagProps({ index })}
                      key={index}
                    />
                  ))
                }
                renderInput={(params) => (
                  <TextField
                    {...params}
                    placeholder="Enter certification"
                    helperText="Type and press Enter to add certification"
                  />
                )}
              />
            </FormControl>

            <FormControl>
              <FormLabel required>Minimum Level of Education</FormLabel>
              <Select
                required
                value={educationLevel}
                onChange={(e) =>
                  setEducationLevel(
                    e.target.value as HighestCompletedEducationLevel,
                  )
                }
              >
                <MenuItem value={HighestCompletedEducationLevel.Doctorate}>
                  Doctorate
                </MenuItem>
                <MenuItem value={HighestCompletedEducationLevel.Masters}>
                  Master's Degree
                </MenuItem>
                <MenuItem value={HighestCompletedEducationLevel.Bachelors}>
                  Bachelor's Degree
                </MenuItem>
                <MenuItem value={HighestCompletedEducationLevel.Associates}>
                  Associate's Degree
                </MenuItem>
                <MenuItem value={HighestCompletedEducationLevel.Certificate}>
                  Vocational Qualification / Certification
                </MenuItem>
                <MenuItem value={HighestCompletedEducationLevel.PostHighSchool}>
                  Post High School
                </MenuItem>
                <MenuItem value={HighestCompletedEducationLevel.HighSchool}>
                  High School Diploma
                </MenuItem>
                <MenuItem value={HighestCompletedEducationLevel.GED}>
                  GED
                </MenuItem>
                <MenuItem
                  value={HighestCompletedEducationLevel.NoFormalEducation}
                >
                  No Formal Education
                </MenuItem>
              </Select>
              <FormHelperText>Select education level</FormHelperText>
            </FormControl>
          </Stack>
        )}
        {activeStep === 3 && (
          <Box>
            <Typography>
              Please review the information below before publishing your job
              posting. You can edit any section by clicking the "Edit" link next
              to it.
            </Typography>
            <Box sx={{ mt: 2 }}>
              <Stack spacing={2} direction="row" alignItems="center">
                <Typography variant="h6">Job Information</Typography>
                <Link component="button" onClick={() => setActiveStep(0)}>
                  Edit
                </Link>
              </Stack>
              <Typography>
                <strong>Job Title:</strong> {jobTitle}
              </Typography>
              <Typography>
                <strong>Job URL:</strong> {jobUrl}
              </Typography>
              <Typography>
                <strong>Industry:</strong> {industry}
              </Typography>
              <Typography>
                <strong>Tech Area:</strong> {techArea}
              </Typography>
              <Typography>
                <strong>Occupation Code (onet-socc):</strong> {occupationCode}
              </Typography>
              <Typography>
                <strong>Application Deadline:</strong>{" "}
                {applicationDeadline
                  ? applicationDeadline.format("MM/DD/YYYY")
                  : ""}
              </Typography>
            </Box>
            <Box sx={{ mt: 2 }}>
              <Stack spacing={2} direction="row" alignItems="center">
                <Typography variant="h6">Employment Information</Typography>
                <Link component="button" onClick={() => setActiveStep(1)}>
                  Edit
                </Link>
              </Stack>
              <Typography>
                <strong>Employment Type:</strong> {employmentType}
              </Typography>
              <Typography>
                <strong>Paid Position:</strong> {paidPosition ? "Yes" : "No"}
              </Typography>
              <Typography>
                <strong>Internship:</strong> {internship ? "Yes" : "No"}
              </Typography>
              <Typography>
                <strong>Apprenticeship:</strong> {apprenticeship ? "Yes" : "No"}
              </Typography>
              <Typography>
                <strong>Location:</strong> {location}
              </Typography>
              <Typography>
                <strong>Relocation Assistance:</strong>{" "}
                {relocation ? "Yes" : "No"}
              </Typography>
              <Typography>
                <strong>H1B Visa Sponsorship:</strong>{" "}
                {visaSponsor ? "Yes" : "No"}
              </Typography>
              <Typography>
                <strong>Work Environment:</strong> {workEnvironment}
              </Typography>
              <Typography>
                <strong>Compensation:</strong>{" "}
                {paidPosition
                  ? "$" +
                    Number(startingPayRange).toLocaleString() +
                    (endingPayRange
                      ? " - $" + Number(endingPayRange).toLocaleString()
                      : "") +
                    (compensationType === "hourly" ? " / hr" : " / year")
                  : "None"}
              </Typography>
              <Typography>
                <strong>Compensation Type:</strong> {compensationType}
              </Typography>
            </Box>
            <Box sx={{ mt: 2 }}>
              <Stack spacing={2} direction="row" alignItems="center">
                <Typography variant="h6">Qualifications</Typography>
                <Link component="button" onClick={() => setActiveStep(2)}>
                  Edit
                </Link>
              </Stack>
              <Typography>
                <strong>Required Skills:</strong>{" "}
                {requiredSkills.map((skill) => skill.skill_name)}
              </Typography>
              <Typography>
                <strong>Training Requirements:</strong> {trainingRequirements}
              </Typography>
              <Typography>
                <strong>Certifications:</strong> {requiredCertifications}
              </Typography>
              <Typography>
                <strong>Education Level:</strong> {educationLevel}
              </Typography>
            </Box>
          </Box>
        )}
        <Grid container sx={{ justifyContent: "space-between", mt: 3 }}>
          <PillButton
            color="secondary"
            disabled={activeStep == 0}
            onClick={handleBack}
          >
            Back
          </PillButton>
          {activeStep !== 3 ? (
            <PillButton
              color="secondary"
              startIcon={<ArrowCircleRightOutlined />}
              onClick={handleNext}
              disabled={!isStepValid()}
            >
              Continue
            </PillButton>
          ) : (
            <PillButton
              color="secondary"
              startIcon={<FileUploadOutlined />}
              onClick={handleSubmit}
              disabled={!isStepValid()}
            >
              {job_posting ? "Update" : "Publish"}
            </PillButton>
          )}
        </Grid>
      </Stack>
    </LocalizationProvider>
  );
}
