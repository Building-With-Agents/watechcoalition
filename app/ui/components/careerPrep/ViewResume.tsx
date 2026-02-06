"use client";
import React, { useEffect, useState } from "react";
import { Button } from "@mui/material";

export default function ViewResume(props: { userId: string }) {
  const [hasUrl, setHasUrl] = useState<boolean>(false);
  useEffect(() => {
    fetchResume(props.userId).then((val) => {
      setHasUrl(val != undefined);
    });
  }, []);
  return (
    <Button
      onClick={async (e) => {
        e.preventDefault();
        const resumeUrl = await fetchResume(props.userId);
        window.open(resumeUrl, "_blank");
      }}
    >
      {hasUrl ? "View" : "Not Found"}
    </Button>
  );
}

async function fetchResume(id: string) {
  const response = await fetch("/api/jobseekers/resume/get/" + id, {
    // Make the request
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });
  if (!response.ok) {
    return undefined;
  }
  return (await response.json()) as string;
}
