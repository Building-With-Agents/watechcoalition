"use client";

import { SkillDTO } from "@/data/dtos/SkillDTO";
import { Button } from "@mui/material";
import { JobRole, JobRoleSkill } from "@prisma/client";
import { useEffect, useState } from "react";
import TextFieldWithAutocomplete from "../mui/TextFieldWithAutocomplete";
interface EmployerFeedbackFormProps {
  jobroleId: string;
}
export default function EmployerFeedbackForm({
  jobroleId,
}: EmployerFeedbackFormProps) {
  const [selectedJobRole, setSelectedJobRole] = useState<
    | (JobRole & {
        skills: (JobRoleSkill & {
          skill: {
            skill_name: string;
          };
        })[];
      })
    | null
  >(null);
  const [extraSkills, setExtraSkills] = useState<SkillDTO[]>([]);
  const [currentSkill, setCurrentSkill] = useState<SkillDTO | null>(null);
  const [skillRatings, setSkillRatings] = useState<{
    [skillId: string]: number;
  }>({});
  useEffect(() => {
    fetch("/api/ict/jobs-by-id/" + jobroleId)
      .then((res) => res.json())
      .then((jsonData) => setSelectedJobRole(jsonData));
  }, []);

  function isFormValid() {
    const allSkillsRated = selectedJobRole?.skills.every(
      (skill) =>
        skillRatings[skill.skillId] !== undefined &&
        skillRatings[skill.skillId] > 0,
    );
    const allExtraSkillsRated = extraSkills.every(
      (skill) =>
        skillRatings[skill.skill_id] !== undefined &&
        skillRatings[skill.skill_id] > 0,
    );
    return allSkillsRated && allExtraSkillsRated;
  }

  const handleSkillRatingChange = (skillId: string, rating: number) => {
    setSkillRatings((prev) => ({
      ...prev,
      [skillId]: rating,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const payload = {
      jobRoleId: selectedJobRole?.id,
      skillRatings,
    };
    console.log("Submitting feedback:", payload);
    try {
      const response = await fetch("/api/employer-feedback", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        // Handle non-2xx responses
        const errorData = await response.json();
        console.error("Error:", errorData.message);
        alert("Failed to submit feedback. Please try again.");
      } else {
        const data = await response.json();
        console.log("Success:", data.message);
        alert("Feedback submitted successfully!");
      }
    } catch (error) {
      console.error("Error during submission:", error);
      alert("An error occurred while submitting feedback. Please try again.");
    }
  };
  const addAdditionalSkills = () => {
    if (currentSkill) {
      if (
        extraSkills.some((sk) => sk.skill_id == currentSkill.skill_id) ||
        selectedJobRole?.skills.some(
          (sjk) => sjk.skillId == currentSkill.skill_id,
        )
      )
        return;
      setExtraSkills((prev) => [...prev, currentSkill]);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6 p-7">
      {/* Skill Ratings */}
      {selectedJobRole && (
        <div>
          <h3 className="font-semibold text-gray-800">
            Rate the importance of each skill (1-5):
          </h3>
          {selectedJobRole.skills.map((skill) => (
            <div key={skill.skillId} className="grid grid-cols-2  my-2">
              <label>{skill.skill.skill_name}</label>
              <select
                className="p-2 border rounded-md"
                value={skillRatings[skill.skillId] || ""}
                onChange={(e) =>
                  handleSkillRatingChange(
                    skill.skillId,
                    parseInt(e.target.value),
                  )
                }
              >
                <option value="" disabled>
                  Select a rating
                </option>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n} -{" "}
                    {
                      [
                        "Not Important at All",
                        "Slightly Important",
                        "Moderately Important",
                        "Very Important",
                        "Critical / Must-Have",
                      ][n - 1]
                    }
                  </option>
                ))}
              </select>
            </div>
          ))}
          {extraSkills.map((skill) => (
            <div key={skill.skill_id} className="grid grid-cols-2  my-2">
              <label>{skill.skill_name}</label>
              <select
                className="p-2 border rounded-md"
                value={skillRatings[skill.skill_id] || ""}
                onChange={(e) =>
                  handleSkillRatingChange(
                    skill.skill_id,
                    parseInt(e.target.value),
                  )
                }
              >
                <option value="" disabled>
                  Select a rating
                </option>
                {[1, 2, 3, 4, 5].map((n) => (
                  <option key={n} value={n}>
                    {n} -{" "}
                    {
                      [
                        "Not Important at All",
                        "Slightly Important",
                        "Moderately Important",
                        "Very Important",
                        "Critical / Must-Have",
                      ][n - 1]
                    }
                  </option>
                ))}
              </select>
            </div>
          ))}
          <div>
            <div className="mb-6">
              <TextFieldWithAutocomplete<SkillDTO>
                apiSearchRoute="/api/skills/vsearch/"
                fieldLabel="Select Additional Skill"
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
            <Button
              type="button"
              onClick={addAdditionalSkills}
              disabled={!currentSkill}
            >
              Add Additional skill
            </Button>
          </div>
        </div>
      )}
      <Button type="submit" disabled={!isFormValid()}>
        Submit Feedback
      </Button>
    </form>
  );
}
