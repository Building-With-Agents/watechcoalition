"use client";

import PillButton from "../PillButton";
import { Add, Close } from "@mui/icons-material";
import { useState } from "react";
import { ButtonProps, Dialog, DialogContent, DialogTitle } from "@mui/material";
import NewJobForm from "./NewJobForm";
import { JobPostCreationDTO } from "@/data/dtos/JobListingDTO";

interface NewJobFormButtonProps extends ButtonProps {
  company_id: string | null;
  onJobCreated?: (job: JobPostCreationDTO) => void;
}

export default function NewJobFormButton({
  company_id,
  onJobCreated,
  onClick,
  children = "Post a New Job",
  color = "secondary",
  startIcon = <Add />,
  ...buttonProps
}: NewJobFormButtonProps) {
  const [open, setOpen] = useState(false);
  const handleClose = () => setOpen(false);

  const handleJobCreated = (newJob: JobPostCreationDTO) => {
    if (onJobCreated) {
      onJobCreated(newJob);
    }
    handleClose();
  };

  return (
    <>
      <PillButton
        color={color}
        startIcon={startIcon}
        onClick={(e) => {
          if (onClick) onClick(e);
          setOpen(true);
        }}
        {...buttonProps}
      >
        {children}
      </PillButton>
      <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
        <DialogTitle variant="h4" sx={{ px: 2, pt: 2 }}>
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
            company_id={company_id}
            job_posting={undefined}
            onJobUpdated={handleJobCreated}
          />
        </DialogContent>
      </Dialog>
    </>
  );
}
