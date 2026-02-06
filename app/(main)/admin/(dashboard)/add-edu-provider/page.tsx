"use client";
import React, { FormEvent, useState } from "react";
import { AddTrainingPartnerDTO } from "@/app/lib/admin/eduProviderPartner";
import AvatarUpload from "@/app/ui/components/AvatarUpload";
import SelectOptionsWithLabel from "@/app/ui/components/SelectOptionsWithLabel";
import { v4 as uuidv4 } from "uuid";
import { EducationLevel } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { Button, Grid } from "@mui/material";
import {
  ArrowCircleRightOutlined,
  HighlightOffOutlined,
} from "@mui/icons-material";

export default function Page() {
  const [eduProviderId, setEduProviderId] = useState(uuidv4());
  const [logoUrl, setLogoUrl] = useState(""); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [initialImageUrl, setInitialImageUrl] = useState(""); // eslint-disable-line @typescript-eslint/no-unused-vars
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const form = event.currentTarget;
    const submitButton = event.currentTarget.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    if (submitButton) submitButton.disabled = true;
    const providerData: AddTrainingPartnerDTO = {
      eduProviderId: uuidv4(),
      eduLevel: formData.get("eduLevel") as EducationLevel,
      providerName: formData.get("providerName") as string,
      contactName: formData.get("contactName") as string,
      contactEmail: formData.get("contactEmail") as string,
      website: formData.get("url") as string,
      mission: formData.get("mission") as string,
      providerDescription: formData.get("providerDescription") as string,
      setsApartStatement: formData.get("setsApartStatement") as string,
      screeningCriteria: formData.get("screeningCriteria") as string,

      recruitingSources: formData.get("recruitingSources") as string,
      programCount: formData.get("programCount") as string,
      cost: formData.get("cost") as string,
      isCoalitionMember: formData.get("isCoalitionMember") === "on",
      isAdminReviewed: true,
      logoUrl: formData.get("logoUrl") as string,
    };
    try {
      const response = await fetch("/api/edu-providers/add", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(providerData), // Send as JSON
      });

      if (!response.ok) {
        // If response is not OK, handle error
        console.error("Failed to create training provider");
        if (submitButton) submitButton.disabled = false;
        return;
      } else {
        // Await the response JSON
        const data = await response.json();
        console.log("training provider created: ", data);

        // Reset form fields
        form.reset();
        setLogoUrl("");
        setInitialImageUrl("");
        setEduProviderId(uuidv4()); // Generate new UUID for next submission
        if (submitButton) submitButton.disabled = false;
      }
    } catch (error) {
      console.error("Error creating training provider:", error);
      if (submitButton) submitButton.disabled = false;
    }
  }

  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <h1 className="text-xl font-bold">Add Training Provider</h1>

      {/* TP Logo Upload */}
      <div className="grid grid-cols-1">
        <label htmlFor="avatarUpload">Upload Training Provider Logo</label>
        <AvatarUpload
          id="avatarUpload"
          fileTypeText="File types: SVG, PNG, JPG, GIF, or WEBP"
          accept=".svg,.png,.jpg,.jpeg,.gif,.webp"
          maxSizeMB={5}
          userId={eduProviderId}
          onImageUpload={(url) => {
            console.log("Received URL in Page.tsx:", url); // Log the received URL
            // Handle the uploaded image URL
            setLogoUrl(url);
            const hiddenInput = document.getElementById(
              "logoUrl",
            ) as HTMLInputElement;
            if (hiddenInput) {
              hiddenInput.value = url;
            }
          }}
          initialImageUrl=""
          apiPath="/api/edu-providers/avatar/upload"
        />
        {/* Hidden input to store avatar URL */}
        <input type="hidden" name="logoUrl" id="logoUrl" />
      </div>

      {/* Provider Name */}
      <div className="grid grid-cols-1">
        <label htmlFor="providerName">Provider Name</label>
        <input type="text" name="providerName" required />
      </div>

      {/* Education Level */}
      <div className="grid grid-cols-1">
        <SelectOptionsWithLabel
          id="eduLevel"
          options={Object.values(EducationLevel)
            .filter((value) => value !== "")
            .map((value) => ({ label: value, value }))}
          placeholder="Select Education Level"
        >
          Education Level
        </SelectOptionsWithLabel>
      </div>

      {/* Contact Name */}
      <div className="grid grid-cols-1">
        <label htmlFor="contactName">Contact Name</label>
        <input type="text" name="contactName" />
      </div>

      {/* Contact Email */}
      <div className="grid grid-cols-1">
        <label htmlFor="contactEmail">Contact Email</label>
        <input type="email" name="contactEmail" />
      </div>

      {/* URL */}
      <div className="grid grid-cols-1">
        <label htmlFor="url">Provider Website</label>
        <input type="url" name="url" />
      </div>

      {/* Mission */}
      <div className="grid grid-cols-1">
        <label htmlFor="mission">Mission Statement</label>
        <textarea name="mission" />
      </div>

      {/* Provider Description */}
      <div className="grid grid-cols-1">
        <label htmlFor="providerDescription">Provider Description</label>
        <textarea name="providerDescription" />
      </div>

      {/* What Sets You Apart */}
      <div className="grid grid-cols-1">
        <label htmlFor="setsApartStatement">What Sets You Apart</label>
        <textarea name="setsApartStatement" />
      </div>

      {/* Screening Criteria */}
      <div className="grid grid-cols-1">
        <label htmlFor="screeningCriteria">Screening Criteria</label>
        <textarea name="screeningCriteria" />
      </div>

      {/* Recruiting Sources */}
      <div className="grid grid-cols-1">
        <label htmlFor="recruitingSources">Recruiting Sources</label>
        <textarea name="recruitingSources" />
      </div>

      {/* Program Count */}
      <div className="grid grid-cols-1">
        <label htmlFor="programCount">Number of Programs</label>
        <input type="number" name="programCount" />
      </div>

      {/* Cost */}
      <div className="grid grid-cols-1">
        <label htmlFor="cost">Cost Details</label>
        <textarea name="cost" />
      </div>

      {/* Is Coalition Member */}
      <div className="grid grid-cols-1">
        <label htmlFor="isCoalitionMember">
          <input type="checkbox" name="isCoalitionMember" /> Is Coalition Member
        </label>
      </div>

      {/* Submit Button */}
      <Grid container spacing={1}>
        <Button
          type="reset"
          variant="outlined"
          startIcon={<HighlightOffOutlined />}
        >
          Reset Form
        </Button>
        <Button
          type="submit"
          endIcon={<ArrowCircleRightOutlined />}
          variant="contained"
        >
          Create Provider
        </Button>
      </Grid>
    </form>
  );
}
