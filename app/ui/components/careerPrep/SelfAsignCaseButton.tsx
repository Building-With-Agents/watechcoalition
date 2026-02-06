"use client";
import Button from "@mui/material/Button";
import { useState } from "react";

export default function SelfAssignCaseButton(props: { jobseekerId: string }) {
  const [claimed, setClaimed] = useState(false);
  const handleClick = async () => {
    try {
      setClaimed(true);
      const response = await fetch("/api/admin/career-prep/self-assign-case", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ jobseekerId: props.jobseekerId }),
      });

      if (!response.ok) {
        alert("Failed to self-assign case:" + (await response.text()));
        setClaimed(false);
      }
    } catch (error) {
      console.error("Error while self-assigning case:", error);
    }
  };
  return (
    <Button onClick={handleClick} disabled={claimed}>
      {claimed ? "Claimed" : "Claim"}
    </Button>
  );
}
