"use client";
import { Button } from "@mui/material";
import { companies, industry_sectors } from "@prisma/client";
import { useEffect, useState } from "react";
import { ArrowCircleRightOutlined } from "@mui/icons-material";
import HighlightOffOutlinedIcon from "@mui/icons-material/HighlightOffOutlined";
import AvatarUpload from "@/app/ui/components/AvatarUpload";

const companyStartInfo: companies = {
  company_id: "",
  industry_sector_id: null,
  company_name: "",
  company_logo_url: null,
  about_us: "",
  company_email: "",
  contact_name: null,
  year_founded: null,
  company_website_url: null,
  company_video_url: null,
  company_phone: null,
  company_mission: null,
  company_vision: null,
  size: "",
  estimated_annual_hires: null,
  is_approved: false,
  createdBy: null,
  createdAt: new Date(),
  updatedAt: new Date(),
  engagementType: "",
};

export default function Page() {
  const [selectedCompany, setSelectedCompany] = useState("");
  const [companies, setCompanies] = useState<companies[]>([]);
  const [industrySectors, setIndustrySectors] = useState<industry_sectors[]>(
    [],
  );
  const [selectedCompanyOgInfo, setSelectedCompanyOginfo] =
    useState<companies>(companyStartInfo);
  const [formData, setFormData] = useState<companies>(companyStartInfo);
  const [logoUrl, setLogoUrl] = useState<string>("");
  const [initialImageUrl, setInitialImageUrl] = useState<string>(""); // eslint-disable-line @typescript-eslint/no-unused-vars

  useEffect(() => {
    fetch("/api/companies/getall")
      .then((res) => res.json())
      .then((jsonData) => setCompanies(jsonData || []))
      .catch((err) => console.error("Error fetching companies:", err));

    fetch("/api/joblistings/sectors")
      .then((res) => res.json())
      .then((jsonData) => setIndustrySectors(jsonData || []))
      .catch((err) => console.error("Error fetching sectors:", err));
  }, []);

  useEffect(() => {
    if (selectedCompany === "") {
      // Clear form if no selection
      setFormData(companyStartInfo);
      setLogoUrl("");
      setInitialImageUrl("");
      setSelectedCompany("");
      return;
    }

    fetch(`/api/companies/${selectedCompany}`)
      .then((res) => res.json())
      .then((r) => {
        setSelectedCompanyOginfo(r.result);
        setFormData(r.result);
        setLogoUrl(r.result.company_logo_url || "");
        setInitialImageUrl(r.result.company_logo_url || "");
        setSelectedCompany(r.result.company_id);
      })
      .catch((err) => console.error("Error fetching company info:", err));
  }, [selectedCompany]);

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) => {
    const { name, value, type } = e.target;
    const checked = "checked" in e.target ? e.target.checked : undefined;
    setFormData((prevData) => ({
      ...prevData,
      [name]:
        type === "checkbox"
          ? checked
          : type === "number"
            ? value === ""
              ? null
              : Number(value)
            : value,
    }));
  };

  const onSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setFormData({ ...formData, company_logo_url: logoUrl });
    try {
      const response = await fetch("/api/companies/update", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });
      if (response.ok) {
        setSelectedCompanyOginfo(formData);
        alert("Company updated successfully");
      } else {
        console.error("Failed to update company");
      }
    } catch (error) {
      console.error("Error submitting form:", error);
    }
  };

  return (
    <main className="w-6/12">
      <div className="grid grid-cols-1">
        <label htmlFor="company">Select Company</label>
        <select
          name="company"
          id="company"
          required
          onChange={(e) => setSelectedCompany(e.target.value)}
        >
          <option value={""}>--Please Select a Company--</option>
          {companies.map((comp) => (
            <option key={comp.company_id} value={comp.company_id}>
              {comp.company_name}
            </option>
          ))}
        </select>
      </div>

      {selectedCompany && (
        <form onSubmit={onSubmit} className="space-y-3">
          {/* Company Logo Upload */}
          <div className="grid grid-cols-1">
            <label htmlFor="avatarUpload">Upload Company Logo</label>
            <AvatarUpload
              id="avatarUpload"
              fileTypeText="File types: SVG, PNG, JPG, GIF, or WEBP"
              accept=".svg,.png,.jpg,.jpeg,.gif,.webp"
              maxSizeMB={5}
              userId={selectedCompany}
              onImageUpload={(url) => {
                setLogoUrl(url);
                setInitialImageUrl(url);
              }}
              initialImageUrl={logoUrl}
              apiPath="/api/companies/avatar/upload"
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="company_name">Company name *</label>
            <input
              type="text"
              name="company_name"
              required
              value={formData.company_name || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="industry_sector_id">
              What Tech Sector does this Company fall under?
            </label>
            <select
              name="industry_sector_id"
              id="sector"
              required
              value={formData.industry_sector_id ?? ""}
              onChange={handleInputChange}
            >
              <option value={""}>--Please Select a Sector--</option>
              {industrySectors.map((sector) => (
                <option
                  key={sector.industry_sector_id}
                  value={sector.industry_sector_id}
                >
                  {sector.sector_title}
                </option>
              ))}
            </select>
          </div>
          <div>
            <input
              type="checkbox"
              name="is_approved"
              checked={formData.is_approved}
              onChange={handleInputChange}
            />
            <label htmlFor="is_approved">Company is approved</label>
          </div>
          <div className="grid grid-cols-1">
            <label htmlFor="about_us">About Company</label>
            <textarea
              name="about_us"
              value={formData.about_us || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="company_mission">Company Mission</label>
            <textarea
              name="company_mission"
              value={formData.company_mission || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="company_vision">Company Vision</label>
            <textarea
              name="company_vision"
              value={formData.company_vision || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="contact_name">Contact name</label>
            <input
              type="text"
              name="contact_name"
              id="contact_name"
              value={formData.contact_name || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="company_email">Contact Email or URL</label>
            <input
              type="text"
              name="company_email"
              value={formData.company_email || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="company_phone">Company Phone</label>
            <input
              type="tel"
              name="company_phone"
              value={formData.company_phone || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="company_website_url">
              Company Website
              <span className="text-xs">(http:// required)</span>
            </label>
            <input
              type="url"
              name="company_website_url"
              placeholder="https://www.example.com"
              value={formData.company_website_url || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="year_founded">Year Founded</label>
            <input
              type="number"
              name="year_founded"
              value={formData.year_founded || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="size">Number Of Employees</label>
            <select
              name="size"
              value={formData.size || ""}
              onChange={handleInputChange}
            >
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
            <label htmlFor="estimated_annual_hires">
              Estimated Annual Hires
            </label>
            <input
              type="number"
              name="estimated_annual_hires"
              value={formData.estimated_annual_hires || ""}
              onChange={handleInputChange}
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={() => setFormData(selectedCompanyOgInfo)}
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
              Update Company
            </Button>
          </div>
        </form>
      )}
    </main>
  );
}
