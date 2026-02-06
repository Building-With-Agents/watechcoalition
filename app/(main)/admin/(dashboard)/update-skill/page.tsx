"use client";
import { FormEvent, useEffect, useState } from "react";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { skill_subcategories } from "@prisma/client";
import { Button, Grid } from "@mui/material";
import { ArrowCircleRightOutlined } from "@mui/icons-material";
import HighlightOffOutlinedIcon from "@mui/icons-material/HighlightOffOutlined";
import TextFieldWithAutocomplete from "@/app/ui/components/mui/TextFieldWithAutocomplete";

export default function UpdateSkillPage() {
  const [skillSubcategories, setSkillSubcategories] =
    useState<skill_subcategories[]>();
  const [currentSkill, setCurrentSkill] = useState<SkillDTO | null>(null);
  const [formData, setFormData] = useState({
    skill_name: "",
    skill_subcategory_id: "",
    skill_info_url: "",
  });

  useEffect(() => {
    fetch("/api/skills/subcategories/get")
      .then((res) => res.json())
      .then((jsonData) => {
        setSkillSubcategories(jsonData);
      });
  }, []);

  useEffect(() => {
    if (currentSkill) {
      setFormData({
        skill_name: currentSkill.skill_name,
        skill_subcategory_id: currentSkill.skill_subcategory_id || "",
        skill_info_url: currentSkill.skill_info_url || "",
      });
    } else {
      setFormData({
        skill_name: "",
        skill_subcategory_id: "",
        skill_info_url: "",
      });
    }
  }, [currentSkill]);

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  async function onUpdateSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const submitButton = event.currentTarget.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    if (submitButton) submitButton.disabled = true;

    if (!currentSkill) {
      alert("No skill selected");
      if (submitButton) submitButton.disabled = false;
      return;
    }

    const updatedSkillData: SkillDTO = {
      skill_id: currentSkill.skill_id,
      skill_name: formData.skill_name,
      skill_subcategory_id: formData.skill_subcategory_id,
      skill_info_url: formData.skill_info_url,
    };

    try {
      const response = await fetch("/api/skills/update", {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updatedSkillData),
      });

      if (response.ok) {
        alert("Skill updated successfully!");
        setCurrentSkill(null);
        setFormData({
          skill_name: "",
          skill_subcategory_id: "",
          skill_info_url: "",
        });
      } else {
        alert("Failed to update skill");
      }
    } catch (error) {
      console.error("Error updating skill:", error);
      alert("Error updating skill");
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  }

  const handleReset = () => {
    setCurrentSkill(null);
    setFormData({
      skill_name: "",
      skill_subcategory_id: "",
      skill_info_url: "",
    });
  };

  return (
    <Grid container gap={4}>
      <div className="w-full max-w-2xl">
        <h2 className="mb-4 text-xl font-bold">Update Skill</h2>

        <div className="mb-6">
          <TextFieldWithAutocomplete<SkillDTO>
            apiSearchRoute="/api/skills/search/"
            fieldLabel="Select Skill to Update"
            value={currentSkill || ""}
            onChange={(_, value) => {
              if (value && typeof value !== "string") {
                setCurrentSkill(value);
              } else {
                setCurrentSkill(null);
              }
            }}
            searchPlaceholder="Search for a skill..."
            getOptionLabel={(option: SkillDTO) => option.skill_name}
            noResultsText="No skills found"
            allowNewOption={false}
            searchingText="Searching skills..."
          />
        </div>

        <form onSubmit={onUpdateSubmit} className="space-y-3">
          <div className="grid grid-cols-1">
            <label htmlFor="skill_name">Skill Name *</label>
            <input
              type="text"
              name="skill_name"
              required
              value={formData.skill_name}
              onChange={(e) => handleInputChange("skill_name", e.target.value)}
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="subcategory">Skill Subcategory *</label>
            <select
              name="subcategory"
              id="subcategory"
              required
              value={formData.skill_subcategory_id}
              onChange={(e) =>
                handleInputChange("skill_subcategory_id", e.target.value)
              }
            >
              <option value="">--Please Select a Subcategory--</option>
              {skillSubcategories?.map((subcat) => (
                <option
                  key={subcat.skill_subcategory_id}
                  value={subcat.skill_subcategory_id}
                >
                  {subcat.subcategory_name}
                </option>
              ))}
            </select>
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="skill_info_url">
              Information URL{" "}
              <span className="text-xs">(http:// required)</span>
            </label>
            <input
              type="url"
              name="skill_info_url"
              placeholder="http://www.example.com"
              value={formData.skill_info_url}
              onChange={(e) =>
                handleInputChange("skill_info_url", e.target.value)
              }
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Button
              type="button"
              variant="outlined"
              startIcon={<HighlightOffOutlinedIcon />}
              onClick={handleReset}
            >
              Reset Form
            </Button>
            <Button
              type="submit"
              endIcon={<ArrowCircleRightOutlined />}
              variant="contained"
              disabled={!currentSkill}
            >
              Update Skill
            </Button>
          </div>
        </form>
      </div>
    </Grid>
  );
}
