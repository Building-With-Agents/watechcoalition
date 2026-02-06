"use client";

import React, { useState } from "react";
import { JobStatus } from "@/app/lib/jobseekerJobTracking";
import { useSession } from "next-auth/react";
import { redirect, usePathname } from "next/navigation";
import PillButton from "../PillButton";
import { Add, Clear } from "@mui/icons-material";
import {
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from "@mui/material";

interface Props {
  id: string;
  job_post_url?: string;
  appliedStatus?: string;
  unPublishDate?: Date;
}

export default function ApplyToJobButton({
  id,
  job_post_url = "",
  appliedStatus = "",
  unPublishDate,
}: Props) {
  const [hasApplied, setHasApplied] = useState<boolean>(
    appliedStatus == JobStatus.Applied ||
      appliedStatus == JobStatus.Contacted ||
      appliedStatus == JobStatus.ScreeningScheduled ||
      appliedStatus == JobStatus.Screened ||
      appliedStatus == JobStatus.Recommended ||
      appliedStatus == JobStatus.Interviewing ||
      appliedStatus == JobStatus.Negotiating ||
      appliedStatus == JobStatus.Accepted ||
      appliedStatus == JobStatus.NoResponse ||
      appliedStatus == JobStatus.NotSelected,
  );
  const [openConfirmWithdraw, setOpenConfirmWithdraw] = useState(false);
  const [isApplying, setIsApplying] = useState(false);
  const [isWithdrawing, setIsWithdrawing] = useState(false);

  const session = useSession();
  const pathname = usePathname();

  const handleApplicationClick = async () => {
    if (!session?.data?.user) {
      const base = window.location.origin;
      const signInUrl = new URL("/signin", base);
      const callbackUrlValue = pathname;
      signInUrl.searchParams.set("callbackUrl", callbackUrlValue);
      redirect(signInUrl.toString());
    }
    try {
      if (!hasApplied) {
        if (job_post_url.length !== 0) {
          const job_post_url_formatted = job_post_url.includes("https://")
            ? job_post_url
            : job_post_url.includes("http://")
              ? job_post_url.replace("http://", "https://")
              : job_post_url.concat("https://", job_post_url);
          window.open(job_post_url_formatted, "_blank");
        }
        setIsApplying(true);
        setHasApplied(true);
        const response = await fetch(`/api/joblistings/apply/${id}`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
        });

        if (!response.ok) {
          setHasApplied(false);
          throw new Error("Failed to update application status.");
        }
      } else {
        setOpenConfirmWithdraw(true);
      }
    } catch (error) {
      console.error("Error updating application:", error);
      if (!appliedStatus) {
        setHasApplied(false);
      }
    } finally {
      setIsApplying(false);
    }
  };

  async function handleConfirmWithdraw() {
    setOpenConfirmWithdraw(false);
    setIsWithdrawing(true);
    setHasApplied(false);
    try {
      const response = await fetch(`/api/joblistings/withdraw/${id}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });
      if (!response.ok) {
        setHasApplied(true);
        throw new Error("Failed to update application status");
      }
    } catch (error) {
      console.error("Error updating application:", error);
      setHasApplied(true);
    } finally {
      setIsWithdrawing(false);
    }
  }

  function handleCancelWithdraw() {
    setOpenConfirmWithdraw(false);
  }

  const isButtonDisabled =
    (unPublishDate && unPublishDate <= new Date()) ||
    appliedStatus == JobStatus.Screened ||
    appliedStatus == JobStatus.Interviewing ||
    appliedStatus == JobStatus.Negotiating ||
    appliedStatus == JobStatus.Accepted ||
    appliedStatus == JobStatus.NoResponse ||
    appliedStatus == JobStatus.NotSelected;

  return (
    <>
      {hasApplied ? (
        <PillButton
          color="error"
          startIcon={<Clear />}
          disabled={isButtonDisabled}
          loading={isWithdrawing}
          onClick={handleApplicationClick}
        >
          {isWithdrawing ? "Withdrawing..." : "Withdraw Consideration"}
        </PillButton>
      ) : (
        <PillButton
          color="secondary"
          startIcon={<Add />}
          disabled={isButtonDisabled}
          loading={isApplying}
          onClick={handleApplicationClick}
        >
          {isApplying ? "Applying..." : "Apply"}
        </PillButton>
      )}
      <Dialog
        open={openConfirmWithdraw}
        onClose={handleCancelWithdraw}
        slotProps={{
          paper: { sx: { borderRadius: "16px", width: "290px", m: 0 } },
        }}
      >
        <DialogTitle sx={{ m: 2, p: 0 }}>Withdraw Consideration?</DialogTitle>
        <DialogContent sx={{ mx: 2, mb: 2, p: 0 }}>
          Are you sure you want to withdraw your consideration for this job? You
          can re-apply if the position is still open.
        </DialogContent>
        <DialogActions
          disableSpacing
          sx={{ m: 2, p: 0, justifyContent: "center", gap: 2 }}
        >
          <PillButton
            size="small"
            color="inherit"
            variant="contained"
            onClick={handleCancelWithdraw}
            sx={{ color: "secondary.main" }}
            loading={isWithdrawing}
          >
            No, Cancel
          </PillButton>
          <PillButton
            size="small"
            color="inherit"
            sx={{
              color: "neutral.black",
              bgcolor: "error.light",
              "&:hover": {
                backgroundColor: "#dfbebd",
              },
            }}
            onClick={handleConfirmWithdraw}
            loading={isWithdrawing}
          >
            {isWithdrawing ? "Withdrawing..." : "Yes, Withdraw"}
          </PillButton>
        </DialogActions>
      </Dialog>
    </>
  );
}
