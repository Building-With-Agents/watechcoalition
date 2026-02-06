"use client";
import { FormEvent, useEffect, useState } from "react";
import { CompanyAdminCreationDTO } from "@/data/dtos/CompanyAdminCreationDTO";
import AvatarUpload from "@/app/ui/components/AvatarUpload";
import { industry_sectors } from "@prisma/client";
import { Button } from "@mui/material";
import { ArrowCircleRightOutlined } from "@mui/icons-material";
import HighlightOffOutlinedIcon from "@mui/icons-material/HighlightOffOutlined";
import { v4 as uuidv4 } from "uuid";
//TODO: Add ability to add a company logo

export default function Page() {
  const [industrySectors, setIndustrySectors] = useState<industry_sectors[]>();
  const [logoUrl, setLogoUrl] = useState(""); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [initialImageUrl, setInitialImageUrl] = useState(""); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [companyId, setCompanyId] = useState("");

  useEffect(() => {
    setCompanyId(uuidv4());

    fetch("/api/joblistings/sectors")
      .then((res) => {
        return res.json();
      })
      .then((jsonData) => {
        setIndustrySectors(jsonData);
      });
  }, []);
  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(event.currentTarget);
    const submitButton = event.currentTarget.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    if (submitButton) submitButton.disabled = true;
    const companyData: CompanyAdminCreationDTO = {
      companyId: companyId,
      companyName: formData.get("company_name") as string,
      aboutUs: formData.get("about_company") as string,
      contactName: formData.get("contact_name") as string,
      companyEmail: formData.get("company_email") as string,
      yearFounded: parseInt(formData.get("year_founded") as string, 10),
      size: formData.get("size") as string,
      isApproved: true,
      companyMission: formData.get("company_mission") as string,
      estimatedAnnualHires: parseInt(formData.get("hires") as string, 10),
      industrySectorId: formData.get("sector") as string,

      companyWebsiteUrl: formData.get("company_url") as string,
      companyVision: formData.get("company_vision") as string,
      companyPhone: formData.get("company_phone") as string,
      logoUrl: formData.get("logoUrl") as string,
    };
    try {
      const response = await fetch("/api/companies/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(companyData), // Send as JSON
      });

      if (response.ok) {
        alert("Company created successfully!");
        form.reset();
        setLogoUrl("");
        setInitialImageUrl("");
        setCompanyId(uuidv4()); // set to new uuid on success in case updating multiple companies at once without reloading page.
      } else {
        alert("Failed to create company");
      }
    } catch (error) {
      console.error("Error creating job listing:", error);
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  }
  return (
    <form onSubmit={onSubmit} className="space-y-3">
      <h1 className="text-xl font-bold">Add Company</h1>

      {/* Company Logo Upload */}
      <div className="grid grid-cols-1">
        <label htmlFor="avatarUpload">Upload Company Logo</label>
        <AvatarUpload
          id="avatarUpload"
          fileTypeText="File types: SVG, PNG, JPG, GIF, or WEBP"
          accept=".svg,.png,.jpg,.jpeg,.gif,.webp"
          maxSizeMB={5}
          userId={companyId}
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
          apiPath="/api/companies/avatar/upload"
        />
        {/* Hidden input to store avatar URL */}
        <input type="hidden" name="logoUrl" id="logoUrl" />
      </div>

      {/* Job Title */}
      <div className="grid grid-cols-1">
        <label htmlFor="company_name">Company name *</label>
        <input type="text" name="company_name" required />
      </div>

      <div className="grid grid-cols-1">
        <label htmlFor="sector">
          What Tech Sector does this Company fall under?
        </label>
        <select name="sector" id="sector" required>
          <option value={""}>--Please Select a Sector--</option>
          {industrySectors?.map((sector) => (
            <option
              key={sector.industry_sector_id}
              value={sector.industry_sector_id}
            >
              {sector.sector_title}
            </option>
          ))}
        </select>
      </div>

      {/* Company about*/}
      <div className="grid grid-cols-1">
        <label htmlFor="about_company">About Company</label>
        <textarea name="about_company" />
      </div>
      {/* Company mission */}
      <div className="grid grid-cols-1">
        <label htmlFor="company_mission">Company Mission</label>
        <textarea name="company_mission" />
      </div>
      {/* Job Description */}
      <div className="grid grid-cols-1">
        <label htmlFor="company_vision">Company Vision</label>
        <textarea name="company_vision" />
      </div>
      <div className="grid grid-cols-1">
        <label htmlFor="contact_name">Contact Name</label>
        <input type="text" name="contact_name" />
      </div>
      {/*company email */}
      <div className="grid grid-cols-1">
        <label htmlFor="company_email">Contact Email or URL</label>
        <input type="text" name="company_email" />
      </div>
      {/*company email */}
      <div className="grid grid-cols-1">
        <label htmlFor="company_phone">Company Phone</label>
        <input type="tel" name="company_phone" />
      </div>
      {/*company url */}
      <div className="grid grid-cols-1">
        <label htmlFor="company_url">
          Company Website <span className="text-xs">(http:// required)</span>
        </label>
        <input
          type="url"
          name="company_url"
          placeholder="https://www.example.com"
        />
      </div>

      {/* year founded */}
      <div className="grid grid-cols-1">
        <label htmlFor="year_founded">Year Founded</label>
        <input type="number" name="year_founded" />
      </div>

      <div className="grid grid-cols-1">
        <label htmlFor="size">Number Of Employees</label>
        {/* <input type="number" name="size"/> */}
        <select name="size">
          <option value={"1-10"}>1-10</option>
          <option value={"11-50"}>1-10</option>
          <option value={"51-200"}>51-200</option>
          <option value={"201-500"}>201-500</option>
          <option value={"501-1000"}>501-1000</option>
          <option value={"1001-5000"}>1001-5000</option>
          <option value={"5000+"}>5000+</option>
        </select>
      </div>

      <div className="grid grid-cols-1">
        <label htmlFor="hires">Estimated Annual Hires</label>
        <input type="number" name="hires" />
      </div>

      {/* Submit Button */}
      <div className="grid grid-cols-2 gap-2">
        <Button
          type="reset"
          variant="outlined"
          startIcon={<HighlightOffOutlinedIcon />}
        >
          Reset Form
        </Button>
        <Button
          type="submit"
          endIcon={<ArrowCircleRightOutlined />}
          variant="contained"
        >
          Create Company
        </Button>
      </div>
    </form>
  );
}
