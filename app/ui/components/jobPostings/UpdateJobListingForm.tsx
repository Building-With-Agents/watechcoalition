"use client";

import { useEffect, useState } from "react";
import { companies as Company } from "@prisma/client";
import {
  Alert,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Snackbar,
  Stack,
} from "@mui/material";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";
import PillButton from "../PillButton";
import { Close } from "@mui/icons-material";
import NewJobForm from "../jobManagement/NewJobForm";

export default function UpdateJobListingForm() {
  const [open, setOpen] = useState(false);
  const handleClose = () => setOpen(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [joblistings, setJobListings] = useState<JobPostCreationDTO[]>([]);
  const [selectedJob, setSelectedJob] = useState<JobPostCreationDTO>();
  const [companyList, setCompanyList] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<string>("");

  useEffect(() => {
    fetch("/api/joblistings/getall")
      .then((res) => res.json())
      .then(setJobListings)
      .catch((err) => console.error("Error fetching job listings:", err));
    fetch("/api/companies/getall")
      .then((res) => res.json())
      .then(setCompanyList)
      .catch((err) => console.error("Error fetching companies:", err));
  }, []);

  const filteredJobs = joblistings
    .filter((job) => job.company_id === selectedCompany)
    .sort((a, b) => a.job_title.localeCompare(b.job_title));

  const handleChange = (event: SelectChangeEvent) => {
    const jobId = event.target.value;
    const job = filteredJobs.find((job) => job.job_posting_id === jobId);
    setSelectedJob(job);
    setOpen(true);
  };

  const handleJobUpdated = (updatedJob: JobPostCreationDTO) => {
    handleClose();
    setOpenSnackbar(true);
    setSelectedJob(undefined);
    setJobListings((prevJobs) =>
      prevJobs.map((job) =>
        job.job_posting_id === updatedJob.job_posting_id ? updatedJob : job,
      ),
    );
  };

  const handleSnackbarClose = (
    event?: React.SyntheticEvent | Event,
    reason?: string,
  ) => {
    if (reason === "clickaway") return;
    setOpenSnackbar(false);
  };

  return (
    <div>
      <p>Select a company and a job.</p>
      <Stack spacing={3} sx={{ mt: 1 }}>
        <FormControl fullWidth>
          <InputLabel id="company-select-label">Company</InputLabel>
          <Select
            fullWidth
            labelId="company-select-label"
            id="company-select"
            value={selectedCompany}
            label="Company"
            onChange={(e) => {
              setSelectedCompany(e.target.value);
              setSelectedJob(undefined);
            }}
          >
            {companyList.map((company) => (
              <MenuItem key={company.company_id} value={company.company_id}>
                {company.company_name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl fullWidth disabled={!selectedCompany}>
          <InputLabel id="job-select-label">Job</InputLabel>
          <Select
            labelId="job-select-label"
            id="job-select"
            value={selectedJob?.job_posting_id || ""}
            label="Job"
            onChange={handleChange}
          >
            {filteredJobs.map((job) => (
              <MenuItem key={job.job_posting_id} value={job.job_posting_id}>
                {job.job_title}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
          <DialogTitle sx={{ px: 2, pt: 2 }}>
            Edit Job Form
            <PillButton
              color="inherit"
              aria-label="close"
              startIcon={<Close />}
              onClick={handleClose}
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
            <NewJobForm
              company_id={selectedCompany}
              job_posting={selectedJob}
              isAdminOrCaseManager={true}
              onJobUpdated={handleJobUpdated}
            />
          </DialogContent>
        </Dialog>
      </Stack>
      <Snackbar
        open={openSnackbar}
        autoHideDuration={2500}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert>Job listing updated successfully!</Alert>
      </Snackbar>
    </div>
  );
}
