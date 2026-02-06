"use client";
import JobSeekerCardView from "@/app/ui/components/JobSeekerCardView";
import { JobSeekerCardViewDTO } from "@/data/dtos/JobSeekerCardViewDTO";
import { useCallback, useEffect, useState } from "react";
import TagsWithAutocomplete from "@/app/ui/components/mui/TagsWithAutocomplete";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { useSearchParams, usePathname, useRouter } from "next/navigation";
import SortDropdown from "@/app/ui/components/mui/SortDropdown";
import Pagination from "@mui/material/Pagination";
import SingleSelectFilter from "@/app/ui/components/mui/SingleSelectFilter";
import { IndustrySectorDropdownDTO } from "@/data/dtos/IndustrySectorDropdownDTO";
import MultipleSelectFilterAutoload from "@/app/ui/components/mui/MultiSelectFilterAutoload";
import TextField from "@mui/material/TextField";
import CircularProgress from "@mui/material/CircularProgress";
import { TrainingProviderDropdownDTO } from "@/data/dtos/TrainingProviderDropdownDTO";
import SingleSelectFilterAutoload from "@/app/ui/components/mui/SingleSelectFilterAutoload";
import { useSession } from "next-auth/react";
import { Role } from "@/data/dtos/UserInfoDTO";
import {
  Box,
  Checkbox,
  FormControlLabel,
  Grid,
  Slider,
  Typography,
} from "@mui/material";
import { HighestCompletedEducationLevel } from "@/data/dtos/JobSeekerProfileCreationDTOs";

const resultsPerPage = 50;

interface JobSeekerQueryResult {
  filteredJobSeekers: JobSeekerCardViewDTO[];
  totalCount: number;
}

async function fetchFilteredJobSeekerCardView(
  skills: string[] = [],
  industrySector: string[] = [],
  educationLevel: string = "",
  trainingProvider: string = "",
  yearsWorkExpMin: number = 0,
  yearsWorkExpMax: number | undefined = undefined,
  zipCode: string = "",
  sortBy: string = "yearsExp",
  hasIntroduction: boolean = false,
  hasAnySkills: boolean = false,
  hasResume: boolean = false,
  maxResults: number = resultsPerPage,
  page: number = 1,
): Promise<JobSeekerQueryResult> {
  if (yearsWorkExpMax == 5) yearsWorkExpMax = undefined;

  const response = await fetch("/api/jobseekers/query", {
    // Make the request
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      skills,
      industrySector,
      educationLevel,
      trainingProvider,
      yearsWorkExpMin,
      yearsWorkExpMax,
      zipCode,
      sortBy,
      hasIntroduction,
      hasAnySkills,
      hasResume,
      maxResults,
      page,
    }),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch data");
  }
  return response.json();
}

async function fetchBookmarkedJobseekers(): Promise<any> {
  const response = await fetch("/api/companies/bookmark/getJobseekers", {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    throw new Error("Failed to fetch data");
  }
  return response.json();
}

export default function TalentSearch() {
  const { data: session } = useSession();
  // Listview data
  const [jobseekers, setJobSeekers] = useState<JobSeekerCardViewDTO[]>([]);
  const [bookmarkedJobseekers, setBookmarkedJobseekers] = useState<string[]>(
    [],
  );
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<boolean>(false);

  // Query data
  const [skillsList, setSkillsList] = useState<string[]>();
  const [industry, setIndustry] = useState<string[]>();
  const [eduLevel, setEduLevel] = useState<string>();
  const [trainingProvider, setTrainingProvider] = useState<string>();
  const [yearsExpMin, setYearsExpMin] = useState<number>();
  const [yearsExpMax, setYearsExpMax] = useState<number>();
  const [zipCode, setZipCode] = useState<string>();
  const [hasIntroduction, setHasIntroduction] = useState<boolean>(false);
  const [hasAnySkills, setHasAnySkills] = useState<boolean>(false);
  const [hasResume, setHasResume] = useState<boolean>(false);

  // Sorting and pagination
  const [sortBy, setSortBy] = useState<string>();
  const [totalResults, setTotalResults] = useState<number>();
  const [page, setPage] = useState<number>();
  const handlePageChange = (
    event: React.ChangeEvent<unknown>,
    value: number,
  ) => {
    setQueryParam("page", encodeURIComponent(value.toString()));
    setPage(value);
  };

  // GET parameter helpers
  const pathname = usePathname();
  const router = useRouter();
  const queryParams = useSearchParams();
  const setQueryParam = useCallback(
    (name: string, value: string) => {
      const params = new URLSearchParams(queryParams.toString());
      if (params.get(name) != value) {
        if (value == "") params.delete(name);
        else params.set(name, value);
        router.push(pathname + "?" + params.toString());
      }
      return;
    },
    [queryParams],
  );

  function getParam(param: string) {
    const retrievedParam: string | null = queryParams.get(param);
    let result: string = "";
    if (retrievedParam != null) result = decodeURIComponent(retrievedParam);
    return result;
  }

  function getArrayParam(param: string) {
    const retrievedParam: string | null = queryParams.get(param);
    let result: string[] = [];
    if (retrievedParam != null && retrievedParam.length > 0)
      result = decodeURIComponent(retrievedParam).split(",");
    return result;
  }

  // Execute query function
  const execQuery = useCallback(async () => {
    setLoading(true);
    setError(false);
    try {
      const data = await fetchFilteredJobSeekerCardView(
        skillsList,
        industry,
        eduLevel,
        trainingProvider,
        yearsExpMin,
        yearsExpMax,
        zipCode,
        sortBy,
        hasIntroduction,
        hasAnySkills,
        hasResume,
        resultsPerPage,
        page,
      );
      setJobSeekers(data.filteredJobSeekers);
      setTotalResults(data.totalCount);
    } catch (error) {
      setError(true);
      console.error("Error fetching job seekers:", error);
    } finally {
      setLoading(false);
    }
  }, [
    skillsList,
    industry,
    eduLevel,
    trainingProvider,
    yearsExpMin,
    yearsExpMax,
    zipCode,
    hasIntroduction,
    hasAnySkills,
    hasResume,
    sortBy,
    page,
  ]);

  useEffect(() => {
    const fetchBookmarked = async () => {
      try {
        if (session?.user.roles.includes(Role.EMPLOYER)) {
          const bookmarkedJobseekers = await fetchBookmarkedJobseekers();
          const jobseekerIds = bookmarkedJobseekers.map(
            (item: any) => item.jobseekerId,
          );

          setBookmarkedJobseekers(jobseekerIds);
        } else {
          setBookmarkedJobseekers([]);
        }
      } catch (error) {
        console.error("Error fetching bookmarked jobs:", error);
      }
    };
    fetchBookmarked();
  }, []);

  const isBookmarked = (jobseekerId: string) => {
    return bookmarkedJobseekers.includes(jobseekerId);
  };

  useEffect(() => {
    // on initial page load, get the params from URL if they exist
    if (
      skillsList == undefined &&
      industry == undefined &&
      eduLevel == undefined &&
      trainingProvider == undefined &&
      yearsExpMin == undefined &&
      yearsExpMax == undefined &&
      zipCode == undefined &&
      sortBy == undefined &&
      page == undefined
    ) {
      setSkillsList(getArrayParam("skills"));
      setIndustry(getArrayParam("industry"));
      setEduLevel(getParam("eduLevel"));
      setTrainingProvider(getParam("trainingProvider"));
      setYearsExpMin(+getParam("yearsExpMin"));
      setYearsExpMax(
        +getParam("yearsExpMax") == 0 ? 5 : +getParam("yearsExpMax"),
      );
      setZipCode(getParam("zipcode"));
      setHasIntroduction(
        getParam("has-introduction") === "true"
          ? true
          : getParam("has-introduction") !== "false"
            ? true
            : false,
      );
      setHasAnySkills(
        getParam("has-any-skills") === "true"
          ? true
          : getParam("has-any-skills") !== "false"
            ? true
            : false,
      );
      setHasResume(
        getParam("has-resume") === "true"
          ? true
          : getParam("has-resume") !== "false"
            ? true
            : false,
      );
      setSortBy(getParam("sort") != "" ? getParam("sort") : "yearsExp");
      const pageParam = getParam("page");
      const pageNumber = pageParam ? +pageParam : 0;
      setPage(pageNumber || 1);
    } else {
      // any other change after initial load should execute a new query
      const timeoutId = setTimeout(() => {
        execQuery();
      }, 500); // simple 0.5sec debounce to avoid rapid queries that could return out of order
      return () => clearTimeout(timeoutId);
    }
  }, [
    skillsList,
    industry,
    eduLevel,
    trainingProvider,
    yearsExpMin,
    yearsExpMax,
    zipCode,
    hasIntroduction,
    hasAnySkills,
    hasResume,
    sortBy,
    page,
  ]);

  return (
    <Box sx={{ mb: 12, mx: { xs: 3, md: 6.25 } }}>
      <h1 className="text-2xl font-bold mb-4">
        Search Results for: {skillsList?.toString().replaceAll(",", ", ")}
      </h1>

      {/* Skill Search Bar */}
      <TagsWithAutocomplete
        apiSearchRoute="/api/skills/search/"
        fieldLabel="Select up to 5 skills to search"
        id="employer-listview-skills"
        maxTags={5}
        searchingText="Searching..."
        noResultsText="No skills found..."
        onChange={function (ev, val) {
          const newVal = (val as SkillDTO[]).map((skill) => skill.skill_name);
          setQueryParam("skills", encodeURIComponent(newVal.toString()));
          setSkillsList(newVal);
        }}
        searchPlaceholder="Skill (ex: Java)"
        getTagLabel={(option: SkillDTO) => option.skill_name}
        getTagLink={(option: SkillDTO) => option.skill_info_url}
        initialTags={getArrayParam("skills")}
      />

      {/* Filters */}
      <Grid container spacing={2} sx={{ my: 2 }}>
        {/* Industry */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <MultipleSelectFilterAutoload
            id="jobseeker-listview-industry"
            label="Industry"
            apiAutoloadRoute="/api/employers/industry-sectors" // TODO: two requests are happening?
            value={getArrayParam("industry")}
            onChange={(event) => {
              setQueryParam(
                "industry",
                encodeURIComponent(event.target.value.toString()),
              );
              if (typeof event.target.value === "string")
                setIndustry([event.target.value]);
              else setIndustry(event.target.value);
            }}
            getOptionLabel={(option: IndustrySectorDropdownDTO) =>
              option.sector_title
            }
          />
        </Grid>

        {/* Education Level */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <SingleSelectFilter
            id="jobseeker-listview-edulevel"
            label="Minimum Degree"
            value={getArrayParam("edulevel")}
            onChange={(event) => {
              setQueryParam(
                "edulevel",
                encodeURIComponent(event.target.value.toString()),
              );
              setEduLevel(event.target.value as string);
            }}
            options={[
              { label: "Any", value: "" },
              {
                label: "Doctorate",
                value: HighestCompletedEducationLevel.Doctorate,
              },
              {
                label: "Master's Degree",
                value: HighestCompletedEducationLevel.Masters,
              },
              {
                label: "Bachelor's Degree",
                value: HighestCompletedEducationLevel.Bachelors,
              },
              {
                label: "Associate's Degree",
                value: HighestCompletedEducationLevel.Associates,
              },
              {
                label: "Vocational Qualification / Certification",
                value: HighestCompletedEducationLevel.Certificate,
              },
              {
                label: "Post High School",
                value: HighestCompletedEducationLevel.PostHighSchool,
              },
              {
                label: "High School Diploma",
                value: HighestCompletedEducationLevel.HighSchool,
              },
              { label: "GED", value: HighestCompletedEducationLevel.GED },
              {
                label: "No Formal Education",
                value: HighestCompletedEducationLevel.NoFormalEducation,
              },
            ]}
          ></SingleSelectFilter>
        </Grid>

        {/* Zip Code */}
        {/* Design has agreed to a text field until we have a better distance measurement system in place */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <TextField
            autoComplete="off"
            label="Full/Partial Zip Code"
            defaultValue={getParam("zipcode")}
            fullWidth
            onChange={(event) => {
              if (!isNaN(Number(event.target.value))) {
                // is it purely numeric chars?
                if (event.target.value.length <= 5) {
                  // and not longer than 5 chars?
                  setQueryParam("zipcode", event.target.value);
                  setZipCode(event.target.value);
                } else {
                  // truncate
                  event.target.value = Number.parseInt(
                    event.target.value.slice(0, 5),
                  ).toString();
                }
              } else {
                // erase non-numeric chars
                const closestInt = Number.parseInt(event.target.value);
                event.target.value = isNaN(closestInt)
                  ? ""
                  : closestInt.toString();
              }
            }}
          />
        </Grid>

        {/* Training Provider */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <SingleSelectFilterAutoload
            id="jobseeker-listview-trainingProvider"
            label="Training Provider"
            apiAutoloadRoute="/api/employers/training-providers"
            value={getParam("trainingProvider")}
            onChange={(event) => {
              setQueryParam(
                "trainingProvider",
                encodeURIComponent(event.target.value.toString()),
              );
              setTrainingProvider(event.target.value as string);
            }}
            getOptionLabel={(option: TrainingProviderDropdownDTO) =>
              option.name
            }
          />
        </Grid>

        {/* Years of Experience */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Typography sx={{ justifySelf: "center" }}>
            Years of Experience
          </Typography>
          <Slider
            size="small"
            value={[
              yearsExpMin ?? 0,
              yearsExpMax ? (yearsExpMax == 0 ? 5 : yearsExpMax) : 5,
            ]}
            onChange={(event: Event, newValue: number | number[]) => {
              if (typeof newValue !== "number") {
                setYearsExpMin(newValue[0]);
                setYearsExpMax(newValue[1]);
                setQueryParam("yearsExpMin", newValue[0].toString());
                setQueryParam("yearsExpMax", newValue[1].toString());
              }
            }}
            getAriaLabel={() => "Years of Experience filter range"}
            getAriaValueText={(value: number, index: number) => {
              return index == 0 ? "min: " + value : "max: " + value;
            }}
            step={1}
            marks={[
              { value: 0, label: "0" },
              { value: 1, label: "1" },
              { value: 2, label: "2" },
              { value: 3, label: "3" },
              { value: 4, label: "4" },
              { value: 5, label: "5+" },
            ]}
            min={0}
            max={5}
            disableSwap
          />
        </Grid>
        {/* Has Introduction, any skills, and/or Resume */}
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <FormControlLabel
            value=""
            control={
              <Checkbox
                checked={hasIntroduction}
                onChange={(event: any) => {
                  const val = event.target.checked;
                  setQueryParam(
                    "has-introduction",
                    encodeURIComponent(val.toString()),
                  );
                  setHasIntroduction(val);
                }}
              />
            }
            label="Has Introduction"
            labelPlacement="end"
          />

          <FormControlLabel
            value=""
            control={
              <Checkbox
                checked={hasAnySkills}
                onChange={(event: any) => {
                  const val = event.target.checked;
                  setQueryParam(
                    "has-any-skills",
                    encodeURIComponent(val.toString()),
                  );
                  setHasAnySkills(val);
                }}
              />
            }
            label="Has any Skills"
            labelPlacement="end"
          />

          <FormControlLabel
            value=""
            control={
              <Checkbox
                checked={hasResume}
                onChange={(event: any) => {
                  const val = event.target.checked;
                  setQueryParam(
                    "has-resume",
                    encodeURIComponent(val.toString()),
                  );
                  setHasResume(val);
                }}
              />
            }
            label="Has Resume"
            labelPlacement="end"
          />
        </Grid>

        {/* Sorting */}
        <Grid
          container
          size={12}
          sx={{ justifyContent: "flex-end", alignItems: "flex-end" }}
        >
          <SortDropdown
            id="jobseeker-listview-sort"
            label="Sort by:"
            value={getParam("sort") == "" ? "newest" : getParam("sort")}
            onChange={(event) => {
              setQueryParam("sort", event.target.value);
              setSortBy(event.target.value);
            }}
            options={[
              // TODO: future preference for sorting by distance, currently achieved by searching with partial zip code
              { label: "Years of Experience", value: "yearsExp" },
              { label: "Highest Degree", value: "highestDegree" },
              { label: "Newest", value: "newest" },
            ]}
          />
        </Grid>
      </Grid>

      {/* Loading */}
      {loading ? (
        <div className="w-full h-full text-center">
          <CircularProgress />
        </div>
      ) : (
        ""
      )}

      {/* Error */}
      {!loading && error ? (
        <div className="w-full h-full text-center text-3xl">
          Error: Invalid Query
        </div>
      ) : (
        ""
      )}

      {/* else, Display Results */}
      {!loading && !error ? (
        <div className="space-y-4">
          {jobseekers.map((jobSeeker: JobSeekerCardViewDTO) => (
            <JobSeekerCardView
              jobseeker={jobSeeker}
              isBookmarked={isBookmarked(jobSeeker.jobseeker_id)}
              key={jobSeeker.jobseeker_id}
            />
          ))}
        </div>
      ) : (
        ""
      )}

      {/* Pagination */}
      <div className="flex justify-center mt-6">
        {!loading && !error ? (
          <div>
            Showing{" "}
            {totalResults == 0
              ? 0
              : resultsPerPage * (page ?? 1) - resultsPerPage + 1}{" "}
            - {Math.min(resultsPerPage * (page ?? 1), totalResults ?? 1)} of{" "}
            {totalResults} total results
          </div>
        ) : (
          ""
        )}
      </div>
      <div className="flex justify-center mt-2 mb-4 phone:mb-0">
        {!loading ? (
          <Pagination
            variant="text"
            color="secondary"
            count={Math.ceil((totalResults ?? 1) / resultsPerPage)}
            page={getParam("page") != "" ? +getParam("page") : 1}
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
        ) : (
          ""
        )}
      </div>
    </Box>
  );
}
