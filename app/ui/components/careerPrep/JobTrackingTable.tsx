"use client";
import Box from "@mui/material/Box";
import Collapse from "@mui/material/Collapse";
import IconButton from "@mui/material/IconButton";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import Radio from "@mui/material/Radio";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Typography from "@mui/material/Typography";
import Paper from "@mui/material/Paper";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import React, { useState } from "react";
import {
  Button,
  CircularProgress,
  FormControlLabel,
  FormLabel,
  Grid,
  Link,
  List,
  ListItem,
  ListItemText,
  RadioGroup,
  TextField,
} from "@mui/material";
import JobStatusDropDown from "./JobStatusDropDown";
import { JobStatus } from "@/app/lib/jobseekerJobTracking";
import ViewResume from "./ViewResume";

interface JobApplication {
  id: string;
  jobPostId: string;
  jobseekerId: string;
  jobStatus: string;
  isBookmarked: boolean | null;
  savedAt: Date;
  appliedDate: Date | null;
  followUpDate: Date | null;
  Jobseekers: {
    jobseeker_id: string;
    assignedPool: string | null;
    highest_level_of_study_completed: string | null;
    user_id: string;
    intro_headline: string | null;
    years_work_exp: number | null;
    users: {
      first_name: string | null;
      last_name: string | null;
      email: string;
    };
  };
}

interface JobPosting {
  job_posting_id: string;
  company_id: string;
  location_id: string;
  employer_id: string | null;
  tech_area_id: string | null;
  sector_id: string | null;
  job_title: string;
  job_description: string;
  is_internship: boolean;
  is_paid: boolean;
  employment_type: string;
  location: string;
  salary_range: string;
  county: string;
  zip: string;
  publish_date: Date;
  unpublish_date: Date;
  job_post_url: string | null;
  assessment_url: string | null;
  jobApplications: JobApplication[];
  companies: {
    company_name: string;
  };
}

interface CandidateRecommendation {
  jobseeker_id: string;
  user_id: string;
  first_name: string | null;
  last_name: string | null;
  email: string;
  final_score: number;
}

interface RowProps {
  row: JobPosting;
}

function Row({ row }: RowProps) {
  const [open, setOpen] = React.useState(false);
  const [recommendations, setRecommendations] = useState<
    CandidateRecommendation[]
  >([]);
  const [isLoadingRecs, setIsLoadingRecs] = useState(false);
  const [recError, setRecError] = useState<string | null>(null);
  const [recommendationsFetched, setRecommendationsFetched] = useState(false);

  const fetchRecommendations = async () => {
    if (isLoadingRecs) return;
    setIsLoadingRecs(true);
    setRecError(null);
    setRecommendations([]);
    setRecommendationsFetched(true);

    try {
      const response = await fetch(
        `/api/admin/career-prep/recommendations/${row.job_posting_id}`,
      );
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.error || `HTTP error! status: ${response.status}`,
        );
      }
      const data: CandidateRecommendation[] | { message: string } =
        await response.json();

      if (Array.isArray(data)) {
        setRecommendations(data);
        if (data.length === 0) {
          setRecError("No suitable candidates found based on skills.");
        }
      } else if (data && data.message) {
        setRecError(data.message);
        setRecommendations([]);
      } else {
        setRecommendations([]);
      }
    } catch (error: any) {
      console.error("Failed to fetch recommendations:", error);
      setRecError(error.message || "Failed to load recommendations.");
      setRecommendations([]);
    } finally {
      setIsLoadingRecs(false);
    }
  };

  return (
    <React.Fragment>
      <TableRow sx={{ "& > *": { borderBottom: "unset" } }}>
        <TableCell>
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          <Link
            href={`/services/joblistings/${row.job_posting_id}`}
            target="_blank"
          >
            {row.job_title}
          </Link>
        </TableCell>
        <TableCell>{row.companies.company_name}</TableCell>
        <TableCell>{row.unpublish_date.toLocaleDateString()}</TableCell>
      </TableRow>
      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto">
            <Box>
              <Typography variant="h6" gutterBottom component="div">
                Job Applications ({row.jobApplications.length})
              </Typography>
              {row.jobApplications.length > 0 ? (
                <TableContainer component={Paper} sx={{ mb: 3 }}>
                  <Table size="small" aria-label="applications">
                    <TableHead>
                      <TableRow>
                        <TableCell>Name</TableCell>
                        <TableCell>Email</TableCell>
                        <TableCell>Years Of Exp</TableCell>
                        <TableCell>Highest Edu</TableCell>
                        <TableCell>Resume</TableCell>
                        <TableCell>Job Status</TableCell>
                        <TableCell>Pool</TableCell>
                        <TableCell>Applied</TableCell>
                        <TableCell>Follow-Up</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {row.jobApplications.map((app) => (
                        <TableRow key={app.id}>
                          <TableCell>
                            <Link
                              href={"/services/jobseekers/" + app.jobseekerId}
                              target="_blank"
                            >
                              {app.Jobseekers.users.first_name}{" "}
                              {app.Jobseekers.users.last_name}
                            </Link>
                          </TableCell>
                          <TableCell>{app.Jobseekers.users.email}</TableCell>
                          <TableCell>{app.Jobseekers.years_work_exp}</TableCell>
                          <TableCell>
                            {app.Jobseekers.highest_level_of_study_completed}
                          </TableCell>
                          <TableCell>
                            <ViewResume userId={app.Jobseekers.user_id} />
                          </TableCell>
                          <TableCell>
                            <JobStatusDropDown
                              currentJobStatus={app.jobStatus as JobStatus}
                              jobAppId={app.id}
                            />
                          </TableCell>
                          <TableCell>{app.Jobseekers.assignedPool}</TableCell>
                          <TableCell>
                            {app.appliedDate
                              ? new Date(app.appliedDate).toLocaleDateString()
                              : ""}
                          </TableCell>
                          <TableCell>
                            {app.followUpDate
                              ? new Date(app.followUpDate).toLocaleDateString()
                              : "N/A"}
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              ) : (
                <Typography variant="body2" sx={{ mb: 3, fontStyle: "italic" }}>
                  No applications received for this job yet.
                </Typography>
              )}
              <Box sx={{ marginTop: 2 }}>
                <Typography variant="h6" gutterBottom component="div">
                  Candidate Recommendations (Based on Skills)
                </Typography>
                <Button
                  variant="contained"
                  onClick={fetchRecommendations}
                  loading={isLoadingRecs}
                  disabled={recommendationsFetched}
                  sx={{ mb: 2 }}
                >
                  Find Matching Candidates
                </Button>

                {isLoadingRecs && !recommendationsFetched && (
                  <Box
                    sx={{ display: "flex", justifyContent: "center", my: 2 }}
                  >
                    <CircularProgress />
                  </Box>
                )}

                {recError && (
                  <Typography color="error" sx={{ my: 2 }}>
                    {recError}
                  </Typography>
                )}

                {!isLoadingRecs &&
                  recommendationsFetched &&
                  recommendations.length === 0 &&
                  !recError && (
                    <Typography
                      variant="body2"
                      sx={{ fontStyle: "italic", my: 2 }}
                    >
                      No candidates found with closely matching skills.
                    </Typography>
                  )}

                {!isLoadingRecs && recommendations.length > 0 && (
                  <Paper
                    elevation={1}
                    sx={{ maxHeight: 300, overflow: "auto" }}
                  >
                    <List dense>
                      {recommendations.map((rec) => (
                        <ListItem key={rec.jobseeker_id} divider>
                          <ListItemText
                            primary={
                              <Link
                                href={`/services/jobseekers/${rec.jobseeker_id}`}
                                target="_blank"
                              >
                                {rec.first_name} {rec.last_name}
                              </Link>
                            }
                            secondary={
                              <>
                                {rec.email} <br />
                                Resume: <ViewResume userId={rec.user_id} />{" "}
                                <br />
                                <Typography
                                  variant="caption"
                                  color="textSecondary"
                                >
                                  Match Score:{" "}
                                  {(rec.final_score * 100).toFixed(1)}%
                                </Typography>
                              </>
                            }
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Paper>
                )}
              </Box>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}

interface JobTrackingTableProps {
  data: JobPosting[];
}

export default function JobTrackingTable({ data }: JobTrackingTableProps) {
  const [filter, setFilter] = useState<string>("");
  const [location, setLocation] = useState<string>("");

  const filteredData = data
    .filter(
      (item) =>
        item.job_title.toLowerCase().includes(filter.toLowerCase()) ||
        item.companies.company_name
          .toLowerCase()
          .includes(filter.toLowerCase()) ||
        item.location.toLowerCase().includes(filter.toLowerCase()),
    )
    .filter((item) => {
      if (!location) return true;
      const jobLocationNormalized = item.location
        .toLowerCase()
        .replace("-", "");
      return jobLocationNormalized.includes(location);
    });

  return (
    <Box sx={{ padding: 2 }}>
      <Box sx={{ display: "flex", gap: 2, mb: 2, flexWrap: "wrap" }}>
        <TextField
          label="Filter by Job Title, Company, or Location"
          variant="outlined"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          fullWidth
        />
        <Grid
          container
          sx={{
            alignItems: "center",
            border: "1px solid",
            borderColor: "neutral.400",
            borderRadius: "4px",
            padding: "0 8px",
          }}
        >
          <FormLabel
            id="location-radio-group-label"
            sx={{ mr: 1, fontSize: "0.8rem", color: "neutral.700" }}
          >
            Location:
          </FormLabel>
          <RadioGroup
            row
            aria-labelledby="location-radio-group-label"
            name="location-filter-group"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            sx={{
              "& .MuiFormControlLabel-root": { marginRight: 1 },
              "& .MuiSvgIcon-root": { fontSize: "1.2rem" },
            }}
          >
            <FormControlLabel
              value=""
              control={<Radio size="small" />}
              label="Any"
            />
            <FormControlLabel
              value="remote"
              control={<Radio size="small" />}
              label="Remote"
            />
            <FormControlLabel
              value="hybrid"
              control={<Radio size="small" />}
              label="Hybrid"
            />
            <FormControlLabel
              value="on-site"
              control={<Radio size="small" />}
              label="On-Site"
            />
          </RadioGroup>
        </Grid>
      </Box>

      <TableContainer component={Paper}>
        <Table aria-label="collapsible job tracking table">
          <TableHead>
            <TableRow>
              <TableCell sx={{ width: "5%" }} />
              <TableCell sx={{ width: "40%" }}>Job Title</TableCell>
              <TableCell sx={{ width: "30%" }}>Company</TableCell>
              <TableCell sx={{ width: "25%" }}>Application Deadline</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredData.length > 0 ? (
              filteredData.map((item) => (
                <Row key={item.job_posting_id} row={item} />
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  No job postings match the current filters.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
