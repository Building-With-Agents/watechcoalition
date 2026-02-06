"use client";
import React, { useEffect, useState } from "react";

import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import {
  Box,
  Card,
  Collapse,
  Divider,
  FormControl,
  Grid,
  IconButton,
  InputLabel,
  Link,
  MenuItem,
  Rating,
  Select,
  SelectChangeEvent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from "@mui/material";
import {
  ArrowDropDown,
  ArrowDropUp,
  Close,
  Mail,
  OpenInNew,
  People,
} from "@mui/icons-material";
import Avatar from "../Avatar";
import PillButton from "../PillButton";
import { JobStatus } from "@/app/lib/jobseekerJobTracking";

type FeedbackTarget = {
  jobseekerJobPostingId: string;
  applicantId: string;
} | null;

export default function EmployerRecommendedCandidatesTable({
  jobs,
}: {
  jobs: JobPostCreationDTO[];
}) {
  const [localJobs, setLocalJobs] = useState<JobPostCreationDTO[]>(jobs);
  const [expandedJobId, setExpandedJobId] = useState<string>();
  const [feedbackTarget, setFeedbackTarget] = useState<FeedbackTarget>(null);
  const [feedbackRating, setFeedbackRating] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState<string>("");

  useEffect(() => {
    setLocalJobs(jobs);
  }, [jobs]);

  const handleShowFeedbackForm = (
    jobseekerJobPostingId: string,
    applicantId: string,
  ) => {
    setFeedbackTarget({ jobseekerJobPostingId, applicantId });
    setFeedbackRating(null);
    setFeedbackText("");
  };

  const handleCancelFeedback = () => {
    setFeedbackTarget(null);
    setFeedbackRating(null);
    setFeedbackText("");
  };

  const handleSubmitFeedback = async () => {
    if (feedbackTarget) {
      const resp = await fetch("/api/joblistings/feedback", {
        method: "POST",
        body: JSON.stringify({
          jobseekerJobPostingId: feedbackTarget.jobseekerJobPostingId,
          rating: feedbackRating,
          comment: feedbackText,
        }),
      });
      if (!resp.ok) {
        return;
      }
      setLocalJobs((prevJobs) =>
        prevJobs.flatMap((job) => {
          if (
            job.jobApplications.some(
              (app) => app.id === feedbackTarget.jobseekerJobPostingId,
            )
          ) {
            const updatedApplications = job.jobApplications.filter(
              (app) => !(app.id === feedbackTarget.jobseekerJobPostingId),
            );
            if (updatedApplications.length === 0) {
              return [];
            }
            return [
              {
                ...job,
                jobApplications: updatedApplications,
              },
            ];
          }
          return [job];
        }),
      );
      handleCancelFeedback();
    }
  };

  const handleStatusChange = async (
    applicationId: string,
    jobPostingId: string,
    newStatus: JobStatus,
  ) => {
    setLocalJobs((prevJobs) =>
      prevJobs.map((job) => {
        if (job.job_posting_id === jobPostingId) {
          return {
            ...job,
            jobApplications: job.jobApplications.map((app) =>
              app.id === applicationId ? { ...app, jobStatus: newStatus } : app,
            ),
          };
        }
        return job;
      }),
    );
    try {
      const resp = await fetch(`/api/joblistings/jobStatus`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jobPostingId: jobPostingId,
          applicationId: applicationId,
          status: newStatus,
        }),
      });

      if (!resp.ok) {
        console.error(
          "Failed to update application status:",
          await resp.text(),
        );
        setLocalJobs(
          jobs.map((job) => ({
            ...job,
            jobApplications: job.jobApplications.map((app) => ({
              ...app,
              jobStatus: app.jobStatus as JobStatus,
            })),
          })),
        );
        alert("Failed to update status. Please try again.");
      } else {
        if (newStatus === JobStatus.Accepted) {
          setLocalJobs((prevJobs) =>
            prevJobs.filter((job) => job.job_posting_id !== jobPostingId),
          );
          if (expandedJobId === jobPostingId) {
            setExpandedJobId(undefined);
          }
        }
      }
    } catch (error) {
      console.error("Error updating application status:", error);
      setLocalJobs(
        jobs.map((job) => ({
          ...job,
          jobApplications: job.jobApplications.map((app) => ({
            ...app,
            status: app.jobStatus as JobStatus,
          })),
        })),
      );
      alert("An error occurred while updating status. Please try again.");
    }
  };

  const handleConnectClicked = async (
    applicationId: string,
    jobPostingId: string,
  ) => {
    try {
      const resp = await fetch(`/api/joblistings/employerconnect`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jobPostingId: jobPostingId,
          applicationId: applicationId,
          status: true,
        }),
      });
      if (!resp.ok) {
        console.error(
          "Error updating employerClickedConnect status:",
          await resp.text(),
        );
      }
    } catch (error) {
      console.error("Error updating employerClickedConnect status:", error);
    }
  };

  const renderApplicantCardContent = (
    job: JobPostCreationDTO,
    application: JobPostCreationDTO["jobApplications"][0],
  ) => {
    const isFeedbackMode =
      feedbackTarget?.jobseekerJobPostingId === application.id &&
      feedbackTarget?.applicantId === application.jobseekerId;

    if (isFeedbackMode) {
      return (
        <Stack spacing={2} sx={{ p: 2 }}>
          <Typography variant="subtitle1" gutterBottom>
            Feedback for {application.Jobseekers.users.first_name}
          </Typography>
          <Box>
            <Typography component="legend">Overall Fit</Typography>
            <Rating
              name={`rating-${application.jobseekerId}`}
              value={feedbackRating}
              onChange={(event, newValue) => {
                setFeedbackRating(newValue);
              }}
            />
          </Box>
          <TextField
            label="Feedback for candidate"
            multiline
            rows={3}
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            variant="outlined"
            fullWidth
          />
          <Stack direction="row" spacing={1} justifyContent="flex-end">
            <PillButton onClick={handleCancelFeedback} color="inherit">
              Cancel
            </PillButton>
            <PillButton
              color="secondary"
              variant="contained"
              onClick={handleSubmitFeedback}
              disabled={feedbackRating === null}
            >
              Submit
            </PillButton>
          </Stack>
        </Stack>
      );
    } else {
      return (
        <Box sx={{ p: 2 }}>
          <Stack direction={"row"} sx={{ justifyContent: "space-between" }}>
            <Grid container spacing={1} sx={{ mb: 2, flexGrow: 1 }}>
              <Avatar
                imgsrc={application.Jobseekers.users.photo_url || undefined}
              />
              <Box>
                <Typography>
                  {application.Jobseekers.users.first_name +
                    " " +
                    application.Jobseekers.users.last_name}
                </Typography>
                <Typography color="textSecondary">
                  {application.Jobseekers.pathways?.pathway_title}
                </Typography>
                <Typography color="textSecondary">
                  {application.postalGeoData?.city +
                    ", " +
                    application.postalGeoData?.stateCode}
                </Typography>
              </Box>
            </Grid>
            <Grid>
              <IconButton
                color="error"
                onClick={() =>
                  handleShowFeedbackForm(
                    application.id,
                    application.jobseekerId,
                  )
                }
                aria-label={`Dismiss candidate ${application.Jobseekers.users.first_name}`}
              >
                <Close />
              </IconButton>
            </Grid>
          </Stack>
          <Typography
            sx={{
              mt: 1,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflowWrap: "break-word",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}
          >
            {application.Jobseekers.intro_headline}
          </Typography>
          <Typography>
            {
              application.Jobseekers.jobseeker_has_skills?.filter((skillObj) =>
                (job.skills?.map((skill) => skill.skill_id) || []).includes(
                  skillObj.skills.skill_id,
                ),
              ).length
            }{" "}
            of {job.skills?.length || 0} skills match
          </Typography>
          <FormControl fullWidth sx={{ mt: 2, mb: 1 }}>
            <InputLabel id={`status-select-label-${application.id}`}>
              Status
            </InputLabel>
            <Select<JobStatus>
              labelId={`status-select-label-${application.id}`}
              id={`status-select-${application.id}`}
              value={application.jobStatus as JobStatus}
              label="Status"
              onChange={(event: SelectChangeEvent<JobStatus>) =>
                handleStatusChange(
                  application.id,
                  job.job_posting_id ?? "",
                  event.target.value as JobStatus,
                )
              }
              size="small"
            >
              <MenuItem
                disabled
                key={JobStatus.Recommended}
                value={JobStatus.Recommended}
              >
                {JobStatus.Recommended}
              </MenuItem>
              <MenuItem
                key={JobStatus.Interviewing}
                value={JobStatus.Interviewing}
              >
                {JobStatus.Interviewing}
              </MenuItem>
              <MenuItem
                key={JobStatus.Negotiating}
                value={JobStatus.Negotiating}
              >
                {JobStatus.Negotiating}
              </MenuItem>
              <MenuItem key={JobStatus.Accepted} value={JobStatus.Accepted}>
                {JobStatus.Accepted}
              </MenuItem>
            </Select>
          </FormControl>
          <Divider sx={{ my: 2 }} />
          <Stack spacing={1}>
            <PillButton
              startIcon={<Mail />}
              color="inherit"
              fullWidth
              href={
                "mailto:" +
                application.Jobseekers.users.email +
                "?subject=" +
                encodeURIComponent(job.job_title)
              }
              onClick={() =>
                handleConnectClicked(application.id, job.job_posting_id ?? "")
              }
              sx={{ color: "secondary.main" }}
            >
              Connect
            </PillButton>
            <PillButton
              startIcon={<OpenInNew />}
              color="secondary"
              fullWidth
              href={"/services/jobseekers/" + application.jobseekerId}
              target="_blank"
            >
              View Portfolio
            </PillButton>
          </Stack>
        </Box>
      );
    }
  };

  if (localJobs.length == 0) {
    return <p>No prescreened applicants currently, check back later</p>;
  }

  return (
    <>
      <Card variant="outlined" sx={{ display: { xs: "none", sm: "block" } }}>
        <TableContainer sx={{ px: 3 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: "secondary.main", fontWeight: "500" }}>
                  Job Title
                </TableCell>
                <TableCell sx={{ color: "secondary.main", fontWeight: "500" }}>
                  Tech Category
                </TableCell>
                <TableCell sx={{ color: "secondary.main", fontWeight: "500" }}>
                  Location
                </TableCell>
                <TableCell sx={{ color: "secondary.main", fontWeight: "500" }}>
                  Expires
                </TableCell>
                <TableCell sx={{ color: "secondary.main", fontWeight: "500" }}>
                  Candidates
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {localJobs.map((job) => (
                <React.Fragment key={job.job_posting_id}>
                  <TableRow
                    key={job.job_posting_id}
                    sx={{ "&:last-child td": { borderBottom: 0 } }}
                  >
                    <TableCell>
                      <Link
                        href={"/services/joblistings/" + job.job_posting_id}
                        color="secondary"
                        sx={{ fontWeight: "500" }}
                      >
                        {job.job_title}
                      </Link>
                    </TableCell>
                    <TableCell sx={{ color: "secondary.main" }}>
                      {job.techArea?.title}
                    </TableCell>
                    <TableCell sx={{ color: "neutral.700" }}>
                      {job.postalGeoData?.city +
                        ", " +
                        job.postalGeoData?.stateCode}
                    </TableCell>
                    <TableCell>
                      {job.unpublish_date?.toLocaleString(undefined, {
                        weekday: "long",
                        month: "short",
                        day: "numeric",
                      })}
                    </TableCell>
                    <TableCell>
                      {job.jobApplications.length > 0 && (
                        <IconButton
                          onClick={() =>
                            setExpandedJobId(
                              expandedJobId === job.job_posting_id
                                ? undefined
                                : job.job_posting_id,
                            )
                          }
                        >
                          {expandedJobId === job.job_posting_id ? (
                            <ArrowDropDown />
                          ) : (
                            <ArrowDropUp />
                          )}
                        </IconButton>
                      )}
                    </TableCell>
                  </TableRow>
                  <TableRow>
                    <TableCell
                      sx={{ paddingBottom: 0, paddingTop: 0 }}
                      colSpan={6}
                    >
                      <Collapse in={expandedJobId !== undefined} timeout="auto">
                        {expandedJobId === job.job_posting_id && (
                          <Grid container spacing={1} sx={{ my: 1 }}>
                            {job.jobApplications.map((application) => (
                              <Grid
                                size={{ xs: 12, sm: 6, md: 4 }}
                                key={
                                  job.job_posting_id + application.jobseekerId
                                }
                              >
                                <Card>
                                  {renderApplicantCardContent(job, application)}
                                </Card>
                              </Grid>
                            ))}
                            <Card component={Grid} size={4} sx={{ p: 2 }}>
                              <Grid
                                container
                                sx={{
                                  height: "100%",
                                  justifyContent: "center",
                                  alignItems: "center",
                                }}
                              >
                                <Stack
                                  sx={{
                                    alignItems: "center",
                                    justifyContent: "space-between",
                                  }}
                                >
                                  <Typography variant="h5" color="secondary">
                                    View more qualified candidates
                                  </Typography>
                                  <People
                                    color="primary"
                                    sx={{ width: 58, height: 58 }}
                                  />
                                </Stack>
                                <PillButton
                                  target="_blank"
                                  href={
                                    "/services/employers/dashboard/talent-search?skills=" +
                                    job.skills?.map((skill) => skill.skill_name)
                                  }
                                  fullWidth
                                  color="secondary"
                                >
                                  View More
                                </PillButton>
                              </Grid>
                            </Card>
                          </Grid>
                        )}
                      </Collapse>
                    </TableCell>
                  </TableRow>
                </React.Fragment>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Card>
      {/* Mobile View */}
      <Card variant="outlined" sx={{ display: { xs: "block", sm: "none" } }}>
        <Stack spacing={1} direction="column" sx={{ pt: 1 }}>
          {localJobs.map((job, index) => (
            <Box key={job.job_posting_id + "sm"} sx={{ px: 2 }}>
              <Stack
                direction="row"
                alignItems="center"
                justifyContent="space-between"
              >
                <Link
                  href={"/services/joblistings/" + job.job_posting_id}
                  color="secondary"
                  sx={{ fontWeight: "500" }}
                >
                  {job.job_title}
                </Link>
                {job.jobApplications.length > 0 && (
                  <IconButton
                    onClick={() =>
                      setExpandedJobId(
                        expandedJobId === job.job_posting_id
                          ? undefined
                          : job.job_posting_id,
                      )
                    }
                  >
                    {expandedJobId === job.job_posting_id ? (
                      <ArrowDropDown />
                    ) : (
                      <ArrowDropUp />
                    )}
                  </IconButton>
                )}
              </Stack>
              <Typography sx={{ color: "secondary.main" }}>
                {job.techArea?.title}
              </Typography>
              <Typography sx={{ color: "neutral.700" }}>
                {job.postalGeoData?.city + ", " + job.postalGeoData?.stateCode}
              </Typography>
              <Typography>
                {job.unpublish_date?.toLocaleString(undefined, {
                  weekday: "long",
                  month: "short",
                  day: "numeric",
                })}
              </Typography>
              <Collapse
                in={expandedJobId === job.job_posting_id}
                timeout="auto"
              >
                <Stack
                  spacing={2}
                  sx={{ justifyContent: "space-around", my: 2 }}
                >
                  {job.jobApplications.map((application) => (
                    <Grid key={job.job_posting_id + application.jobseekerId}>
                      <Card>
                        {renderApplicantCardContent(job, application)}
                      </Card>
                    </Grid>
                  ))}
                  <Card component={Grid} sx={{ p: 2 }}>
                    <Stack
                      sx={{
                        alignItems: "center",
                        justifyContent: "center",
                        spacing: 2,
                        pb: 2,
                      }}
                    >
                      <Typography
                        variant="h6"
                        color="secondary"
                        align="center"
                        sx={{ mb: 1 }}
                      >
                        View more qualified candidates
                      </Typography>
                      <People
                        color="primary"
                        sx={{ width: 48, height: 48, mb: 2 }}
                      />
                      <PillButton
                        fullWidth
                        color="secondary"
                        href={
                          "/services/employers/dashboard/talent-search?skills=" +
                          job.skills?.map((skill) => skill.skill_name)
                        }
                      >
                        View More
                      </PillButton>
                    </Stack>
                  </Card>
                </Stack>
              </Collapse>
              {index !== localJobs.length - 1 && (
                <Divider
                  variant="middle"
                  orientation="horizontal"
                  sx={{ my: 1 }}
                />
              )}
            </Box>
          ))}
        </Stack>
      </Card>
    </>
  );
}
