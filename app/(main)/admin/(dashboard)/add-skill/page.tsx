"use client";
import { FormEvent, useEffect, useState } from "react";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import { skill_subcategories } from "@prisma/client";
import { Button, Grid } from "@mui/material";
import { ArrowCircleRightOutlined } from "@mui/icons-material";
import HighlightOffOutlinedIcon from "@mui/icons-material/HighlightOffOutlined";
import UploadFileIcon from "@mui/icons-material/UploadFile";

export default function Page() {
  const [skillSubcategories, setSkillSubcategories] =
    useState<skill_subcategories[]>();
  const [csvFile, setCsvFile] = useState<File | null>(null);

  useEffect(() => {
    fetch("/api/skills/subcategories/get")
      .then((res) => {
        return res.json();
      })
      .then((jsonData) => {
        setSkillSubcategories(jsonData);
      });
  }, []);

  const createAndAppendSubcategory = async (
    subcategoryName: string,
  ): Promise<string> => {
    try {
      const newSubcategory = {
        skill_subcategory_id: "",
        subcategory_name: subcategoryName,
        subcategory_description: "",
      };

      const response = await fetch("/api/skills/subcategories/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newSubcategory),
      });

      if (!response.ok) {
        throw new Error("Failed to create subcategory");
      }

      const result = await response.json();

      setSkillSubcategories((prev) => (prev ? [...prev, result] : [result]));

      return result.skill_subcategory_id;
    } catch (error) {
      console.error("Error creating subcategory:", error);
      throw error;
    }
  };

  const validateForm = (formData: FormData): boolean => {
    const skillName = formData.get("skill_name") as string;
    const subcategory = formData.get("subcategory") as string;
    const skillInfoUrl = formData.get("skill_info_url") as string;

    if (!skillName.trim()) {
      alert("Please enter a skill name");
      return false;
    }

    if (!subcategory) {
      alert("Please select a subcategory");
      return false;
    }

    if (!skillInfoUrl.trim()) {
      alert("Please enter a valid information URL");
      return false;
    }

    try {
      new URL(skillInfoUrl);
    } catch {
      alert("Please enter a valid URL starting with https://");
      return false;
    }

    return true;
  };

  async function onSingleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(event.currentTarget);
    if (!validateForm(formData)) {
      return;
    }

    const submitButton = event.currentTarget.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    if (submitButton) submitButton.disabled = true;

    const skillData: SkillDTO[] = [
      {
        skill_id: "",
        skill_name: formData.get("skill_name") as string,
        skill_subcategory_id: formData.get("subcategory") as string,
        skill_info_url: (formData.get("skill_info_url") as string) || "",
      },
    ];

    try {
      const response = await fetch("/api/skills/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(skillData),
      });

      if (response.ok) {
        alert("Skill created successfully!");
        form.reset();
      } else {
        alert("Failed to create skill");
      }
    } catch (error) {
      console.error("Error creating skill:", error);
    } finally {
      if (submitButton) submitButton.disabled = false;
    }
  }

  const handleCsvUpload = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!csvFile) return;

    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const text = e.target?.result as string;
        const rows = text.split("\n");
        const headers = rows[0].split(",").map((header) => header.trim());

        // Validate CSV headers
        const requiredHeaders = ["skill_name", "subcategory", "skill_info_url"];
        const hasRequiredHeaders = requiredHeaders.every((header) =>
          headers.includes(header),
        );

        if (!hasRequiredHeaders) {
          alert(
            "CSV must include columns: skill_name, subcategory, skill_info_url",
          );
          return;
        }

        // Parse CSV data
        const skillData: SkillDTO[] = [];
        for (const row of rows.slice(1).filter((row) => row.trim())) {
          const values = row.split(",").map((value) => value.trim());
          const rowData: Record<string, string> = {};
          headers.forEach((header, index) => {
            rowData[header] = values[index] || "";
          });

          let subcategoryId: string;
          const matchingSubcat = skillSubcategories?.find(
            (subCat) =>
              subCat.subcategory_name.toLowerCase() ===
              rowData.subcategory.toLowerCase(),
          );

          if (matchingSubcat) {
            subcategoryId = matchingSubcat.skill_subcategory_id;
          } else {
            try {
              // Create new subcategory and get its ID
              subcategoryId = await createAndAppendSubcategory(
                rowData.subcategory,
              );
            } catch {
              alert(`Failed to create subcategory: ${rowData.subcategory}`);
              continue;
            }
          }

          skillData.push({
            skill_id: "",
            skill_name: rowData.skill_name,
            skill_subcategory_id: subcategoryId,
            skill_info_url: rowData.skill_info_url || "",
          });
          console.log(skillData);
        }

        const response = await fetch("/api/skills/create", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(skillData),
        });

        if (response.ok) {
          alert("Skills imported successfully!");
          setCsvFile(null);
          const fileInput = document.getElementById(
            "csvFile",
          ) as HTMLInputElement;
          if (fileInput) fileInput.value = "";
        } else {
          alert("Failed to import skills");
        }
      } catch (error) {
        console.error("Error processing CSV:", error);
        alert("Error processing CSV file");
      }
    };

    reader.readAsText(csvFile);
  };

  return (
    <Grid container gap={4}>
      <div>
        <h2 className="mb-4 text-xl font-bold">Add Single Skill</h2>
        <form onSubmit={onSingleSubmit} className="space-y-3">
          <div className="grid grid-cols-1">
            <label htmlFor="skill_name">Skill Name *</label>
            <input
              type="text"
              name="skill_name"
              id="skill_name"
              required
              minLength={2}
              maxLength={200}
              className="rounded-xs border p-2"
            />
          </div>

          <div className="grid grid-cols-1">
            <label htmlFor="subcategory">Skill Subcategory *</label>
            <select
              name="subcategory"
              id="subcategory"
              required
              className="rounded-xs border p-2"
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
              Information URL *{" "}
              <span className="text-xs">(https:// required)</span>
            </label>
            <input
              type="url"
              name="skill_info_url"
              id="skill_info_url"
              required
              pattern="https://.*"
              placeholder="https://www.example.com"
              className="rounded-xs border p-2"
            />
          </div>

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
              Create Skill
            </Button>
          </div>
        </form>
      </div>
      <div>
        <h2 className="mb-4 text-xl font-bold">Bulk Import Skills</h2>
        <form onSubmit={handleCsvUpload} className="space-y-3">
          <div className="grid grid-cols-1">
            <label htmlFor="csvFile">Upload CSV File</label>
            <div>
              <input
                type="file"
                id="csvFile"
                accept=".csv"
                onChange={(e) => setCsvFile(e.target.files?.[0] || null)}
                className="py-2"
                required
              />
            </div>
            <p className="mt-1 text-sm text-gray-600">
              CSV must include columns: skill_name, subcategory_name,
              skill_info_url
            </p>
          </div>

          <Button
            type="submit"
            variant="contained"
            startIcon={<UploadFileIcon />}
            disabled={!csvFile}
          >
            Import Skills
          </Button>
        </form>
      </div>
    </Grid>
  );
}
