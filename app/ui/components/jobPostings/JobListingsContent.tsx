"use client";
import JobListingCardView from "@/app/ui/components/jobPostings/JobListingCardView";
import { useCallback, useEffect, useState, useMemo } from "react";
import { useSearchParams, usePathname, useRouter } from "next/navigation";
import Pagination from "@mui/material/Pagination";
import CircularProgress from "@mui/material/CircularProgress";
import TagsWithAutocomplete from "@/app/ui/components/mui/TagsWithAutocomplete";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import {
  Box,
  Checkbox,
  Divider,
  FormControlLabel,
  Grid,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from "@mui/material";
import MultipleSelectFilterAutoload from "@/app/ui/components/mui/MultiSelectFilterAutoload";
import { IndustrySectorDropdownDTO } from "@/data/dtos/IndustrySectorDropdownDTO";
import { JobListingCardViewDTO } from "@/data/dtos/JobListingCardViewDTO";
import SingleSelectFilterAutoload from "../mui/SingleSelectFilterAutoload";
import { TechnologyAreaDropdownDTO } from "@/data/dtos/TechnologyAreaDropdownDTO";
import { MultipleSelectCheckmarks } from "../mui/MultiSelectFilter";
import { EmploymentType } from "@/app/lib/admin/jobTracking";
import { useSession } from "next-auth/react";
import { Role } from "@/data/dtos/UserInfoDTO";
import Link from "next/link";
import { ArrowBack } from "@mui/icons-material";

const resultsPerPage = 50;

interface JobListingQueryResult {
  filteredJobPostings: JobListingCardViewDTO[];
  totalCount: number;
}

async function fetchJobPosts(
  jobTitle: string = "",
  bookmarked: boolean = false,
  skills: string[] = [],
  city: string[] = [],
  profession: string = "",
  careerServicesOffered: boolean = false,
  industrySector: string[] = [],
  employmentType: string[] = [],
  sortBy: string = "publish_date",
  maxResults: number = resultsPerPage,
  page: number = 1,
): Promise<JobListingQueryResult> {
  const response = await fetch("/api/joblistings/query", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      jobTitle,
      bookmarked,
      skills,
      city,
      profession,
      careerServicesOffered,
      industrySector,
      employmentType,
      sortBy,
      maxResults,
      page,
    }),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch data");
  }
  return response.json();
}

export default function JobListingsContent() {
  const { data: session } = useSession();
  // Listview data
  const [value, setValue] = useState(0);
  const [joblistings, setJobListings] = useState<JobListingCardViewDTO[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  // Query data (initialized with empty defaults)
  const [jobTitle, setJobTitle] = useState<string>("");
  const [skillsList, setSkillsList] = useState<string[]>([]);
  const [city, setCity] = useState<string[]>([]);
  const [profession, setProfession] = useState<string>("");
  const [industry, setIndustry] = useState<string[]>([]);
  const [employmentType, setEmploymentType] = useState<string[]>([]);
  const [careerServicesOffered, setCareerServicesOffered] =
    useState<boolean>(false);

  // Sorting and pagination
  const [totalResults, setTotalResults] = useState<number>(0);
  const [page, setPage] = useState<number>(1);

  const pathname = usePathname();
  const router = useRouter();
  const queryParams = useSearchParams();

  const setQueryParam = useCallback(
    (name: string, value: string) => {
      const params = new URLSearchParams(queryParams.toString());
      if (params.get(name) !== value) {
        if (value === "") params.delete(name);
        else params.set(name, value);
        router.push(`${pathname}?${params.toString()}`);
      }
    },
    [queryParams, pathname, router],
  );

  const getParam = useCallback(
    (param: string) => {
      const retrieved = queryParams.get(param);
      return retrieved ? decodeURIComponent(retrieved) : "";
    },
    [queryParams],
  );

  const getArrayParam = useCallback(
    (param: string) => {
      const retrieved = queryParams.get(param);
      return retrieved && retrieved.length > 0
        ? decodeURIComponent(retrieved).split(",")
        : [];
    },
    [queryParams],
  );

  // Initialize state from URL parameters only once (on mount)
  useEffect(() => {
    setJobTitle(getParam("jobTitle"));
    setSkillsList(getArrayParam("skills"));
    setProfession(getParam("profession"));
    setCareerServicesOffered(
      getParam("career-services-offered") === "true" ? true : false,
    );
    setEmploymentType(getArrayParam("employment-type"));
    setIndustry(getArrayParam("industry"));
    setCity(getArrayParam("city"));
    const pageParam = +getParam("page");
    setPage(pageParam > 0 ? pageParam : 1);
  }, []);

  const execQuery = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await fetchJobPosts(
        jobTitle,
        value === 1,
        skillsList,
        city,
        profession,
        careerServicesOffered,
        industry,
        employmentType,
        "publish_date",
        resultsPerPage,
        page,
      );
      setJobListings(data.filteredJobPostings);
      setTotalResults(data.totalCount);
    } catch (err) {
      setError(true);
      console.error("Error fetching job listings:", err);
    } finally {
      setLoading(false);
    }
  }, [
    jobTitle,
    value,
    skillsList,
    city,
    profession,
    careerServicesOffered,
    industry,
    employmentType,
    page,
  ]);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      execQuery();
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [
    jobTitle,
    skillsList,
    profession,
    careerServicesOffered,
    employmentType,
    industry,
    city,
    page,
    execQuery,
  ]);

  const handleTabChange = useCallback(
    (event: React.SyntheticEvent, newValue: number) => {
      setValue(newValue);
    },
    [],
  );

  const handlePageChange = useCallback(
    (event: React.ChangeEvent<unknown>, value: number) => {
      setQueryParam("page", encodeURIComponent(value.toString()));
      setPage(value);
    },
    [setQueryParam],
  );

  const handleJobTitleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const val = event.target.value;
      setQueryParam("jobTitle", val);
      setJobTitle(val);
    },
    [setQueryParam],
  );

  const handleSkillsChange = useCallback(
    (event: any, val: any) => {
      const newVal = (val as SkillDTO[]).map((skill) => skill.skill_name);
      setQueryParam("skills", encodeURIComponent(newVal.toString()));
      setSkillsList(newVal);
    },
    [setQueryParam],
  );

  const handleCityChange = useCallback(
    (event: any, val: any) => {
      const newVal = val.map((v: { city: string }) => v.city);
      setQueryParam("city", encodeURIComponent(newVal.toString()));
      setCity(newVal);
    },
    [setQueryParam],
  );

  const handleProfessionChange = useCallback(
    (event: any) => {
      const val = event.target.value;
      setQueryParam("profession", encodeURIComponent(val.toString()));
      setProfession(val);
    },
    [setQueryParam],
  );

  const handleCareerServicesChange = useCallback(
    (event: any) => {
      const val = event.target.checked;
      setQueryParam(
        "career-services-offered",
        encodeURIComponent(val.toString()),
      );
      setCareerServicesOffered(val);
    },
    [setQueryParam],
  );

  const handleIndustryChange = useCallback(
    (event: any) => {
      const newValue = event.target.value;
      setQueryParam("industry", encodeURIComponent(newValue.toString()));
      setIndustry(typeof newValue === "string" ? [newValue] : newValue);
    },
    [setQueryParam],
  );

  const handleEmploymentTypeChange = useCallback(
    (event: any) => {
      const newValue = event.target.value;
      setQueryParam("employment-type", encodeURIComponent(newValue.toString()));
      setEmploymentType(typeof newValue === "string" ? [newValue] : newValue);
    },
    [setQueryParam],
  );

  const totalPages = useMemo(
    () => Math.ceil((totalResults || 1) / resultsPerPage),
    [totalResults],
  );

  return (
    <Box sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}>
      {session?.user.roles.includes(Role.JOBSEEKER) && (
        <Link href="/services/jobseekers/dashboard">
          <ArrowBack sx={{ width: "16px", height: "16px" }} /> My Dashboard
        </Link>
      )}
      <Stack spacing={2.5}>
        <Typography variant="h3" sx={{ color: "secondary.main" }}>
          Jobs
        </Typography>

        {/* Job Title Search Bar */}
        <TextField
          autoComplete="off"
          label="Full/Partial Job Title"
          fullWidth
          defaultValue={getParam("jobTitle")}
          onChange={handleJobTitleChange}
          sx={{ mb: 3 }}
        />

        {/* Skill Search Bar */}
        <TagsWithAutocomplete
          apiSearchRoute="/api/skills/search/"
          fieldLabel="Select up to 5 skills to search"
          id="employer-listview-skills"
          maxTags={5}
          searchingText="Searching..."
          noResultsText="No skills found..."
          onChange={handleSkillsChange}
          searchPlaceholder="Skill (ex: Java)"
          getTagLabel={(option: SkillDTO) => option.skill_name}
          value={skillsList.map((skillName) => ({
            skill_id: "",
            skill_name: skillName,
            skill_info_url: "",
          }))}
        />

        {/* Filters */}
        <Grid container spacing={2}>
          {/* City */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <TagsWithAutocomplete
              apiSearchRoute="/api/postal-geo-data/city/search/"
              fieldLabel="Select up to 5 cities to search"
              id="jobseeker-listview-city"
              maxTags={5}
              searchingText="Searching..."
              noResultsText="No cities found..."
              onChange={handleCityChange}
              searchPlaceholder="City (ex: Seattle)"
              getTagLabel={(option: { city: string }) => option.city}
              value={city.map((city) => ({ city: city }))}
            />
          </Grid>
          {/* Profession */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <SingleSelectFilterAutoload
              id="jobseeker-listview-profession"
              label="Profession"
              apiAutoloadRoute="/api/employers/technology-areas"
              value={getParam("profession")}
              onChange={handleProfessionChange}
              getOptionLabel={(option: TechnologyAreaDropdownDTO) =>
                option.title
              }
            />
          </Grid>
          {/* Industry */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <MultipleSelectFilterAutoload
              id="jobseeker-listview-industry"
              label="Industry"
              apiAutoloadRoute="/api/employers/industry-sectors"
              value={getArrayParam("industry")}
              onChange={handleIndustryChange}
              getOptionLabel={(option: IndustrySectorDropdownDTO) =>
                option.sector_title
              }
            />
          </Grid>
          {/* Employment Type */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <MultipleSelectCheckmarks
              label="Employment Type"
              value={getArrayParam("employment-type")}
              onChange={handleEmploymentTypeChange}
              options={Object.values(EmploymentType).map((type) => ({
                label: type,
                value: type,
              }))}
            />
          </Grid>
          {/* Employer Partner Jobs */}
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <FormControlLabel
              value=""
              control={
                <Checkbox
                  checked={careerServicesOffered}
                  onChange={handleCareerServicesChange}
                />
              }
              label="Employer Partner Jobs"
              labelPlacement="end"
            />
          </Grid>
        </Grid>

        {session?.user.roles.includes(Role.JOBSEEKER) && (
          <Box sx={{ borderBottom: 1, borderColor: "divider" }}>
            <Tabs
              value={value}
              onChange={handleTabChange}
              aria-label="Job Search or Saved Jobs"
            >
              <Tab id="tab-0" label="Job Search" />
              <Tab id="tab-1" label="Saved Jobs" />
            </Tabs>
          </Box>
        )}

        {/* Loading */}
        {loading && (
          <div className="h-full w-full text-center">
            <CircularProgress />
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="h-full w-full text-center text-3xl">
            Error: Invalid Query
          </div>
        )}

        {/* Display Results */}
        {!loading && !error && (
          <Stack spacing={2} divider={<Divider />}>
            {joblistings.map((joblisting: JobListingCardViewDTO) => (
              <JobListingCardView
                joblisting={joblisting}
                key={joblisting.job_posting_id}
              />
            ))}
          </Stack>
        )}

        {/* Pagination Info */}
        {!loading && !error && (
          <div className="mt-6 flex justify-center">
            <div>
              Showing{" "}
              {totalResults === 0
                ? 0
                : resultsPerPage * page - resultsPerPage + 1}{" "}
              - {Math.min(resultsPerPage * page, totalResults)} of{" "}
              {totalResults} total results
            </div>
          </div>
        )}

        {/* Pagination */}
        <div className="pb-2 mt-2 flex justify-center phone:pb-8">
          {!loading && (
            <Pagination
              variant="text"
              color="secondary"
              count={totalPages}
              page={page}
              onChange={handlePageChange}
              sx={{
                "& .MuiPaginationItem-root:not(.Mui-selected):not(.MuiPaginationItem-ellipsis):not(.MuiPaginationItem-previousNext)":
                  {
                    bgcolor: "neutral.200",
                    "&:hover": { bgcolor: "neutral.100" },
                  },
                "& .MuiPaginationItem-root:not(.Mui-selected)": {
                  color: "secondary.main",
                },
              }}
            />
          )}
        </div>
      </Stack>
    </Box>
  );
}
