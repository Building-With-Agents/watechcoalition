"use client";

import {
  Card,
  Table,
  TableContainer,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Stack,
  Box,
  Typography,
  Divider,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Link,
} from "@mui/material";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import { useEffect, useState } from "react";
import {
  ArrowDropDown,
  ArrowDropUp,
  Close,
  DeleteOutlined,
  EditOutlined,
} from "@mui/icons-material";
import NewJobForm from "./NewJobForm";
import PillButton from "../PillButton";

interface JobListingsTableProps {
  company_id: string;
  jobs: JobPostCreationDTO[];
  onJobUpdated?: (job: JobPostCreationDTO, action: "update" | "delete") => void;
}
export default function JobListingsTable({
  company_id,
  jobs,
  onJobUpdated,
}: JobListingsTableProps) {
  const [localJobs, setLocalJobs] = useState<JobPostCreationDTO[]>(jobs);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState<JobPostCreationDTO | null>(
    null,
  );
  const [expandedJobId, setExpandedJobId] = useState<string>();

  useEffect(() => {
    setLocalJobs(jobs);
  }, [jobs]);

  const handleActionChange = async (event: any, job: JobPostCreationDTO) => {
    if (event.target.value === "edit") {
      setSelectedJob(job);
      setEditDialogOpen(true);
    } else if (event.target.value === "delete") {
      if (job.job_posting_id) {
        try {
          setLocalJobs((currentJobs) =>
            currentJobs.filter((j) => j.job_posting_id !== job.job_posting_id),
          );
          const response = await fetch(
            `/api/joblistings/delete/${job.job_posting_id}`,
            {
              method: "DELETE",
              headers: {
                "Content-Type": "application/json",
              },
            },
          );
          if (!response.ok) {
            throw new Error(`Error: ${response.status}`);
          }
          if (onJobUpdated) {
            onJobUpdated(job, "delete");
          }
        } catch (error) {
          setLocalJobs((currentJobs) => [...currentJobs, job]);
          console.error("Error deleting job post:", error);
        }
      }
    }
  };

  const handleJobUpdated = (updatedJob: JobPostCreationDTO) => {
    setLocalJobs((currentJobs) =>
      currentJobs.map((job) =>
        job.job_posting_id === updatedJob.job_posting_id ? updatedJob : job,
      ),
    );
    if (onJobUpdated) {
      onJobUpdated(updatedJob, "update");
    }
    handleCloseDialog();
  };

  const handleCloseDialog = () => {
    setEditDialogOpen(false);
    setSelectedJob(null);
  };

  return (
    <>
      {/* Desktop View */}
      <Card variant="outlined" sx={{ display: { xs: "none", sm: "block" } }}>
        <TableContainer sx={{ px: 3 }}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: "secondary.main", fontWeight: "500" }}>
                  Action
                </TableCell>
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
                  Status
                </TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {localJobs.map((job) => (
                <TableRow
                  hover
                  key={job.job_posting_id}
                  sx={{ "&:last-child td": { borderBottom: 0 } }}
                >
                  <TableCell
                    sx={{ color: "secondary.main", fontWeight: "500" }}
                  >
                    <FormControl fullWidth>
                      <InputLabel
                        id={`action-select-label-${job.job_posting_id}`}
                      >
                        Action
                      </InputLabel>
                      <Select
                        labelId={`action-select-label-${job.job_posting_id}`}
                        id={`action-select-${job.job_posting_id}`}
                        label="Action"
                        value={""}
                        onChange={(event) => handleActionChange(event, job)}
                      >
                        <MenuItem value={"edit"}>Edit</MenuItem>
                        <MenuItem value={"delete"}>Delete</MenuItem>
                      </Select>
                    </FormControl>
                  </TableCell>
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
                  <TableCell sx={{ color: "neutral.700" }}>{job.zip}</TableCell>
                  <TableCell>
                    {job.unpublish_date?.toLocaleString(undefined, {
                      weekday: "long",
                      month: "short",
                      day: "numeric",
                    })}
                  </TableCell>
                  {job.unpublish_date && new Date() > job.unpublish_date ? (
                    <TableCell sx={{ color: "warning.main" }}>
                      Expired
                    </TableCell>
                  ) : (
                    <TableCell sx={{ color: "success.main" }}>Active</TableCell>
                  )}
                </TableRow>
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
                <Typography>
                  <Link
                    color="secondary"
                    href={"/services/joblistings/" + job.job_posting_id}
                  >
                    {job.job_title}
                  </Link>
                </Typography>
                <IconButton
                  onClick={() =>
                    setExpandedJobId(
                      expandedJobId === job.job_posting_id
                        ? undefined
                        : job.job_posting_id,
                    )
                  }
                >
                  {expandedJobId ? <ArrowDropDown /> : <ArrowDropUp />}
                </IconButton>
              </Stack>
              <Typography>{job.techArea?.title}</Typography>
              {job.unpublish_date && new Date() > job.unpublish_date ? (
                <Typography sx={{ color: "warning.main", mb: 1 }}>
                  Expired
                </Typography>
              ) : (
                <Typography sx={{ color: "success.main", mb: 1 }}>
                  Active
                </Typography>
              )}
              {expandedJobId === job.job_posting_id && (
                <Stack direction="row" spacing={1} sx={{ my: 1 }}>
                  <PillButton
                    startIcon={<EditOutlined />}
                    color="inherit"
                    onClick={() =>
                      handleActionChange({ target: { value: "edit" } }, job)
                    }
                    sx={{ color: "secondary.main" }}
                  >
                    Edit
                  </PillButton>
                  <PillButton
                    startIcon={<DeleteOutlined />}
                    color="error"
                    onClick={() =>
                      handleActionChange({ target: { value: "delete" } }, job)
                    }
                  >
                    Delete
                  </PillButton>
                </Stack>
              )}
              {index !== jobs.length - 1 && (
                <Divider variant="middle" orientation="horizontal" />
              )}
            </Box>
          ))}
        </Stack>
      </Card>

      <Dialog
        open={editDialogOpen}
        onClose={handleCloseDialog}
        fullWidth
        maxWidth="md"
      >
        <DialogTitle variant="h4">
          Edit Job Form
          <PillButton
            color="inherit"
            aria-label="close"
            startIcon={<Close />}
            onClick={handleCloseDialog}
            sx={{
              position: "absolute",
              right: 8,
              top: 16,
              color: "secondary.main",
            }}
          >
            Close
          </PillButton>
        </DialogTitle>
        <DialogContent>
          {selectedJob && (
            <NewJobForm
              company_id={company_id}
              job_posting={selectedJob}
              onJobUpdated={handleJobUpdated}
            />
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
