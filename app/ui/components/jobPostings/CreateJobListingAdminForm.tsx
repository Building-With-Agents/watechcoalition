"use client";
import { useEffect, useState } from "react";
import { companies } from "@prisma/client";
import {
  Box,
  Dialog,
  DialogContent,
  DialogTitle,
  FormControl,
  FormLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
  Snackbar,
  Alert,
} from "@mui/material";
import PillButton from "../PillButton";
import { Close } from "@mui/icons-material";
import NewJobForm from "../jobManagement/NewJobForm";

export default function CreateJobListingAdminForm() {
  const [open, setOpen] = useState(false);
  const handleClose = () => setOpen(false);
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const [companies, setCompanies] = useState<companies[]>();
  const [selectedCompany, setSelectedCompany] = useState<string>("");

  useEffect(() => {
    fetch("/api/companies/getall")
      .then((res) => res.json())
      .then((jsonData) => setCompanies(jsonData));
  }, []);

  const handleChange = (event: SelectChangeEvent) => {
    setSelectedCompany(event.target.value as string);
    setOpen(true);
  };

  const handleSnackbarClose = (
    event?: React.SyntheticEvent | Event,
    reason?: string,
  ) => {
    if (reason === "clickaway") return;
    setOpenSnackbar(false);
  };

  return (
    <Box>
      <FormControl>
        <FormLabel>What Company Does this listing belong to?</FormLabel>
        <Select
          required
          value={selectedCompany}
          label="Company"
          onChange={handleChange}
        >
          {companies?.map((comp) => (
            <MenuItem key={comp.company_id} value={comp.company_id}>
              {comp.company_name}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle sx={{ px: 2, pt: 2 }}>
          New Job Form
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
            job_posting={undefined}
            isAdminOrCaseManager={true}
            onJobUpdated={() => {
              handleClose();
              setOpenSnackbar(true);
              setSelectedCompany("");
            }}
          />
        </DialogContent>
      </Dialog>
      <Snackbar
        open={openSnackbar}
        autoHideDuration={2500}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert>Job listing created successfully!</Alert>
      </Snackbar>
    </Box>
  );
}
