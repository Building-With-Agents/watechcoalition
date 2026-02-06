"use client";
import { FormEvent, useState } from "react";
import { Button, Grid } from "@mui/material";
import { ArrowCircleRightOutlined } from "@mui/icons-material";

export default function Page() {
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSingleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    try {
      const response = await fetch("/api/admin/generate-skill-embeddings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (response.ok) {
        const body = await response.json();
        alert(
          `All skill embeddings created successfully:
          ${JSON.stringify(body, null, 2)}`,
        );
      } else {
        alert("Failed to create All skill embeddings");
      }
    } catch (error) {
      console.error("Error creating All skill embeddings:", error);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Grid container gap={4}>
      <div>
        <h2 className="mb-4 text-xl font-bold">
          Generate all Skill embeddings
        </h2>
        <p>Note: Do not run this if you don't know what you are doing.</p>
        <form onSubmit={onSingleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-2">
            <Button
              disabled={isSubmitting}
              type="submit"
              endIcon={<ArrowCircleRightOutlined />}
              variant="contained"
              color="error"
            >
              Generate
            </Button>
          </div>
        </form>
      </div>
    </Grid>
  );
}
