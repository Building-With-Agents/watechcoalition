"use client";
import React, { useState, useEffect } from "react";
import * as pdfjsLib from "pdfjs-dist";
import { SkillDTO } from "@/data/dtos/SkillDTO";
import {
  Box,
  Button,
  CircularProgress,
  FormControl,
  Alert,
  TextField,
  Typography,
  List,
  Divider,
  Card,
  CardContent,
  Grid,
  Chip,
  Link,
} from "@mui/material";
import Skills from "@/app/ui/components/Skills";

type MatchedSkillDetailFrontend = {
  job_skill_name: string;
  seeker_skill_name: string;
  score: number;
};

type RecommendedCandidate = {
  jobseeker_id: string;
  user_id: string;
  first_name: string | null;
  last_name: string | null;
  email: string;
  final_score: number;
  matched_skills: MatchedSkillDetailFrontend[];
  resume_url?: string | null;
  hasResume: boolean;
  analysis?: string | null;
  analysisLoading?: boolean;
};

const PDF_WORKER_URL = "/pdf.worker.min.mjs";

export default function Page() {
  const [jobDescription, setJobDescription] = useState<string>("");
  const [skills, setSkills] = useState<SkillDTO[]>([]);
  const [candidates, setCandidates] = useState<RecommendedCandidate[]>([]);
  const [isLoadingSkills, setIsLoadingSkills] = useState<boolean>(false);
  const [isLoadingCandidates, setIsLoadingCandidates] =
    useState<boolean>(false);
  const [isAnalyzingResumes, setIsAnalyzingResumes] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [pdfWorkerError, setPdfWorkerError] = useState<string | null>(null);

  useEffect(() => {
    try {
      pdfjsLib.GlobalWorkerOptions.workerSrc = PDF_WORKER_URL;
    } catch (e) {
      console.error("Failed to set PDF worker source:", e);
      setPdfWorkerError(
        "Failed to configure PDF processing library. Resume analysis may not work.",
      );
    }
  }, []);

  const parsePdf = async (fileBuffer: ArrayBuffer): Promise<string> => {
    if (pdfWorkerError || !pdfjsLib.getDocument) {
      throw new Error(pdfWorkerError || "PDF library not initialized.");
    }
    try {
      const loadingTask = pdfjsLib.getDocument({ data: fileBuffer });
      const pdf = await loadingTask.promise;
      let fullText = "";
      for (let i = 1; i <= pdf.numPages; i++) {
        const page = await pdf.getPage(i);
        const textContent = await page.getTextContent();
        if (textContent?.items && Array.isArray(textContent.items)) {
          const pageText = textContent.items
            .filter(
              (item: any) =>
                typeof item === "object" &&
                item !== null &&
                typeof item.str === "string",
            )
            .map((item: any) => item.str)
            .join(" ");
          fullText += pageText + "\n\n";
        }
      }
      const trimmedText = fullText.trim();
      if (!trimmedText) {
        throw new Error("No text could be extracted from the PDF.");
      }
      return trimmedText;
    } catch (err: any) {
      console.error("Error parsing PDF:", err);
      throw new Error(`Error reading PDF: ${err.message || "Unknown error"}`);
    }
  };

  const handleFetchSkillsAndCandidates = async () => {
    if (!jobDescription.trim()) {
      setError("Job description cannot be empty.");
      return;
    }
    setIsLoadingSkills(true);
    setIsLoadingCandidates(false);
    setIsAnalyzingResumes(false);
    setError(null);
    setPdfWorkerError(null);
    setSkills([]);
    setCandidates([]);

    try {
      const skillsResponse = await fetch("/api/skills/parse-text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ text: jobDescription }),
      });

      if (!skillsResponse.ok) {
        const errorData = await skillsResponse.json();
        throw new Error(
          errorData.message ||
            errorData.error ||
            `Skill parsing failed: ${skillsResponse.status}`,
        );
      }

      const parsedSkills: SkillDTO[] = await skillsResponse.json();
      setSkills(parsedSkills);

      if (parsedSkills.length === 0) {
        setError(
          "No skills were extracted from the job description. Cannot find candidates.",
        );
        setIsLoadingSkills(false);
        return;
      }
      setIsLoadingSkills(false);

      setIsLoadingCandidates(true);
      const skillIds = parsedSkills.map((skill) => skill.skill_id);

      const candidatesResponse = await fetch(
        "/api/admin/career-prep/recommendations/by-skills",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ skillIds }),
        },
      );

      if (!candidatesResponse.ok) {
        const errorData = await candidatesResponse.json();
        throw new Error(
          errorData.message ||
            `Fetching candidates failed: ${candidatesResponse.status}`,
        );
      }

      const recommendedCandidates: RecommendedCandidate[] =
        await candidatesResponse.json();

      if (
        recommendedCandidates.length === 0 ||
        (recommendedCandidates as any).message
      ) {
        setError(
          (recommendedCandidates as any).message ||
            "No matching candidates found for the extracted skills.",
        );
        setCandidates([]);
        setIsLoadingCandidates(false);
      } else {
        const candidatesWithAnalysisState = recommendedCandidates.map((c) => ({
          ...c,
          analysis: null,
          analysisLoading: false,
          resume_url: null,
        }));
        setCandidates(candidatesWithAnalysisState);
        setIsLoadingCandidates(false);

        if (candidatesWithAnalysisState.length > 0) {
          setIsAnalyzingResumes(true);
          const analysisPromises = candidatesWithAnalysisState.map(
            async (candidate) => {
              if (!candidate.hasResume) {
                setCandidates((prev) =>
                  prev.map((c) =>
                    c.jobseeker_id === candidate.jobseeker_id
                      ? {
                          ...c,
                          analysisLoading: false,
                        }
                      : c,
                  ),
                );
                return;
              }
              setCandidates((prev) =>
                prev.map((c) =>
                  c.jobseeker_id === candidate.jobseeker_id
                    ? { ...c, analysisLoading: true }
                    : c,
                ),
              );
              try {
                const resumeUrlResponse = await fetch(
                  `/api/jobseekers/resume/get/${candidate.user_id}`,
                );
                if (!resumeUrlResponse.ok) {
                  const errorData = await resumeUrlResponse
                    .json()
                    .catch(() => ({}));
                  throw new Error(
                    errorData.message ||
                      `Failed to fetch resume URL: ${resumeUrlResponse.status}`,
                  );
                }
                const resumeBlobUrl = await resumeUrlResponse.json();

                if (!resumeBlobUrl) {
                  throw new Error("Resume URL not found for candidate.");
                }
                setCandidates((prev) =>
                  prev.map((c) =>
                    c.jobseeker_id === candidate.jobseeker_id
                      ? { ...c, resume_url: resumeBlobUrl }
                      : c,
                  ),
                );

                const resumeBlobResponse = await fetch(resumeBlobUrl);
                if (!resumeBlobResponse.ok) {
                  throw new Error(
                    `Failed to fetch resume content: ${resumeBlobResponse.status}`,
                  );
                }
                const resumePdfBuffer = await resumeBlobResponse.arrayBuffer();

                const resumeText = await parsePdf(resumePdfBuffer);

                const analysisResponse = await fetch(
                  "/api/admin/career-prep/analyze-match",
                  {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ resumeText, jobDescription }),
                  },
                );

                if (!analysisResponse.ok) {
                  const errorData = await analysisResponse
                    .json()
                    .catch(() => ({}));
                  throw new Error(
                    errorData.message ||
                      `Analysis API failed: ${analysisResponse.status}`,
                  );
                }
                const analysisData = await analysisResponse.json();

                setCandidates((prev) =>
                  prev.map((c) =>
                    c.jobseeker_id === candidate.jobseeker_id
                      ? {
                          ...c,
                          analysis: analysisData.analysis,
                          analysisLoading: false,
                        }
                      : c,
                  ),
                );
              } catch (analysisErr: any) {
                console.error(
                  `Failed to analyze resume for ${candidate.email}:`,
                  analysisErr,
                );
                setCandidates((prev) =>
                  prev.map((c) =>
                    c.jobseeker_id === candidate.jobseeker_id
                      ? {
                          ...c,
                          analysisLoading: false,
                        }
                      : c,
                  ),
                );
              }
            },
          );
          await Promise.allSettled(analysisPromises);
          setIsAnalyzingResumes(false);
        }
      }
    } catch (e: any) {
      console.error("Operation failed:", e);
      setError(e.message || "An unexpected error occurred. Please try again.");
    } finally {
      setIsLoadingSkills(false);
      setIsLoadingCandidates(false);
      setIsAnalyzingResumes(false);
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Job Description Candidate Matcher
      </Typography>

      <FormControl fullWidth sx={{ mb: 2 }}>
        <TextField
          multiline
          rows={10}
          value={jobDescription}
          onChange={(e) => setJobDescription(e.target.value)}
          placeholder="Enter job description..."
          disabled={
            isLoadingSkills || isLoadingCandidates || isAnalyzingResumes
          }
        />
      </FormControl>

      <Button
        variant="contained"
        color="primary"
        onClick={handleFetchSkillsAndCandidates}
        loading={isLoadingSkills || isLoadingCandidates || isAnalyzingResumes}
        sx={{ mb: 2 }}
      >
        Find Matching Candidates
      </Button>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {pdfWorkerError && !error && (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          onClose={() => setPdfWorkerError(null)}
        >
          {pdfWorkerError}
        </Alert>
      )}

      {skills.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <Typography variant="h5" gutterBottom>
            Extracted Skills
          </Typography>
          <List dense>
            <Skills skillsList={skills} maxNumSkills={0} />
          </List>
        </Box>
      )}

      <Divider sx={{ my: 3 }} />

      <Box>
        <Typography variant="h5" gutterBottom>
          Matched Candidates
        </Typography>
        {isLoadingCandidates && !isLoadingSkills && (
          <CircularProgress sx={{ display: "block", margin: "auto", my: 2 }} />
        )}

        {!isLoadingCandidates &&
          candidates.length === 0 &&
          !error &&
          skills.length > 0 && (
            <Typography variant="body1">
              No candidates found for the extracted skills.
            </Typography>
          )}
        {!isLoadingCandidates && candidates.length > 0 && (
          <>
            <Typography component="div">
              {" "}
              {candidates.map((candidate) => (
                <React.Fragment key={candidate.email}>
                  {candidate.email}{" "}
                </React.Fragment>
              ))}
            </Typography>
            <Grid container spacing={2}>
              {candidates.map((candidate) => (
                <Grid key={candidate.jobseeker_id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Link
                        target="_blank"
                        href={"/services/jobseekers/" + candidate.jobseeker_id}
                      >
                        <Typography variant="h6">
                          {candidate.first_name || "N/A"}{" "}
                          {candidate.last_name || ""}
                        </Typography>
                      </Link>
                      <Typography color="textSecondary">
                        Email: {candidate.email}
                      </Typography>
                      <Typography color="textSecondary">
                        Match Score: {(candidate.final_score * 100).toFixed(2)}%
                      </Typography>
                      <Grid container spacing={2}>
                        <Grid size={{ xs: 12, md: 4 }}>
                          {candidate.matched_skills &&
                            candidate.matched_skills.length > 0 && (
                              <>
                                <Typography
                                  variant="subtitle2"
                                  sx={{ mt: 1, mb: 0.5 }}
                                >
                                  Matched Skills (job ⇒ jobseeker):
                                </Typography>
                                {candidate.matched_skills.map(
                                  (skillMatch, idx) => (
                                    <Box
                                      key={
                                        candidate.user_id +
                                        skillMatch.job_skill_name +
                                        idx
                                      }
                                      sx={{ p: 0.5 }}
                                    >
                                      <Chip
                                        color="primary"
                                        label={skillMatch.job_skill_name}
                                      />
                                      ⇒
                                      <Chip
                                        label={skillMatch.seeker_skill_name}
                                        sx={{ mr: 2 }}
                                      />
                                      {(skillMatch.score * 100).toFixed(1)}%
                                    </Box>
                                  ),
                                )}
                              </>
                            )}
                        </Grid>
                        {candidate.analysisLoading && (
                          <Box
                            sx={{
                              mt: 1,
                              display: "flex",
                              alignItems: "center",
                            }}
                          >
                            <CircularProgress size={20} sx={{ mr: 1 }} />
                            <Typography variant="body2">
                              Analyzing resume...
                            </Typography>
                          </Box>
                        )}
                        {candidate.analysis && !candidate.analysisLoading && (
                          <Grid size={{ xs: 12, md: "grow" }}>
                            <Typography variant="subtitle2">
                              Match Analysis (from resume):
                            </Typography>
                            <Typography
                              variant="body2"
                              sx={{
                                whiteSpace: "pre-wrap",
                                mt: 0.5,
                                border: "1px solid",
                                borderColor: "neutral.300",
                                p: 1,
                                borderRadius: 1,
                              }}
                            >
                              {candidate.analysis}
                            </Typography>
                          </Grid>
                        )}
                      </Grid>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </>
        )}
      </Box>
    </Box>
  );
}
