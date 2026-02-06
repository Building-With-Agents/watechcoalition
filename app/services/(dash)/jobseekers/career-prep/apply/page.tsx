"use client";

import {
  Alert,
  Box,
  Checkbox,
  Chip,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  FormLabel,
  MenuItem,
  Paper,
  Select,
  Snackbar,
  TextField,
  Typography,
  Radio,
  RadioGroup,
  Stack,
} from "@mui/material";
import PillButton from "@/app/ui/components/PillButton";
import { useSession } from "next-auth/react";
import React, { ChangeEvent, useEffect, useState } from "react";
import Confetti from "@/app/ui/components/Confetti";
import "@/app/ui/profile-creation.css";
import { CareerPrepPathways } from "@/app/lib/admin/careerPrep";
import { HighestCompletedEducationLevel } from "@/data/dtos/JobSeekerProfileCreationDTOs";

/* --- constants ------------------------------------------------------------ */

interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  isWAResident: boolean;

  pathway: string;
  highestEducation: string;
  currentlyEnrolledDegree: boolean;
  degreeCompletionWindow: string;

  collegeName: string;
  degreeProgram: string;

  hasTrainingProgram: boolean;
  trainingProvider?: string;

  hasCertifications: boolean;
  certifications: string[];

  weekdayAvailabilityRank: string[];
  timeblockAvailabilityRank: string[];
}

const DEGREE_PROGRAM_OPTIONS = [
  "Application Development",
  "Artificial Intelligence",
  "Business Administration, Management and Operations",
  "Computer and Information Sciences, General",
  "Computer Engineering",
  "Computer/Information Technology Administration and Management",
  "Computer Science",
  "Computer Software and Media Applications",
  "Cybersecurity",
  "Data Management and Analysis",
  "Data Science",
  "Engineering, General",
  "Healthcare Informatics",
  "Information Systems & Technology",
  "Information Technology",
  "Network Systems Administration",
  "Software Development",
  "Software Engineering",
  "Statistics",
  "Other",
] as const;

const TRAINING_PROVIDER_PROGRAMS = [
  "Ada Developers Academy",
  "Career Connect SW ESD 112",
  "CodeDay x MinT",
  "Computing For All (CFA)",
  "North Central ESD 171",
  "Per Scholas Seattle",
  "PNW Cyber Challenge Games",
  "Riipen",
  "Washington Vets2Tech (WaV2T)",
  "Year Up Puget Sound",
  "Other",
] as const;

const DEGREE_WINDOW = [
  "0-3 months",
  "3-6 months",
  "6-9 months",
  "9-12 months",
  "12+ months",
] as const;

const CERTIFICATION_OPTIONS = [
  "AWS Certified Cloud Practitioner",
  "AWS Certified Developer",
  "AWS Certified Solutions Architect",
  "Cardiopulmonary Resuscitation (CPR) Certification",
  "Certified Ethical Hacker",
  "Certified Information Systems Security Professional",
  "Certified Scrum Master",
  "Cisco Certified Network Associate",
  "CompTIA A+",
  "CompTIA Certification",
  "CompTIA Network+",
  "CompTIA Security+",
  "CompTIA Security+ CE",
  "Enterprise Desktop Administrator (Microsoft  Certified IT Professional)",
  "GIAC Certifications",
  "Google Data Analytics Certificate",
  "Microsoft Certified: Azure Fundamentals",
  "Microsoft Certified Professional",
  "Oracle Java Certification",
  "Project Management Professional Certificate",
  "SAS Certification",
  "Security Clearance",
  "Six Sigma Green Belt",
  "Software Development Engineer in Test",
  "Other",
] as const;

const WEEKDAYS = [
  "Monday",
  "Tuesday",
  "Wednesday",
  "Thursday",
  "Friday",
] as const;

const TIMEBLOCKS = [
  "Morning (9-11am)",
  "Afternoon (1-3pm)",
  "Mid-day (11am-1pm)",
  "Late-afternoon (3-5pm)",
  "Evening (5-7pm)",
] as const;

/* --- ranking UI (radio-based) -------------------------------------------- */

/** Move an item to a specific index to keep ranks unique. */
function moveToIndex(list: string[], id: string, toIndex: number) {
  const next = list.slice();
  const from = next.indexOf(id);
  if (from === -1 || toIndex < 0 || toIndex >= next.length) return list;
  next.splice(from, 1);
  next.splice(toIndex, 0, id);
  return next;
}

/** One row showing the label and N radio buttons for position 1..N. */
function RankRow({
  id,
  total,
  currentIndex,
  onChangeIndex,
}: {
  id: string;
  total: number;
  currentIndex: number; // 0-based
  onChangeIndex: (idx: number) => void;
}) {
  return (
    <Box
      sx={{
        px: 2,
        py: 1.25,
        mb: 1,
        border: "1px solid",
        borderColor: "divider",
        borderRadius: 2,
        bgcolor: "background.paper",
        display: "flex",
        alignItems: "center",
        gap: 2,
      }}
    >
      <Box sx={{ flex: 1 }}>{id}</Box>
      <RadioGroup
        row
        name={`rank-${id}`}
        value={currentIndex + 1}
        onChange={(_, val) => {
          const n = Number(val);
          if (!Number.isNaN(n)) onChangeIndex(n - 1);
        }}
      >
        {Array.from({ length: total }, (_, i) => i + 1).map((rank) => (
          <FormControlLabel
            key={rank}
            value={rank}
            control={<Radio size="small" />}
            label={rank}
          />
        ))}
      </RadioGroup>
    </Box>
  );
}

/** List wrapper that maintains array order based on radio selections. */
function RankList({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string[];
  onChange: (next: string[]) => void;
}) {
  const total = value.length;
  return (
    <FormControl component="fieldset" sx={{ mb: 2, width: "100%" }}>
      <FormLabel sx={{ mb: 1 }}>{label}</FormLabel>
      <Box>
        {value.map((id, idx) => (
          <RankRow
            key={id}
            id={id}
            total={total}
            currentIndex={idx}
            onChangeIndex={(toIdx) => onChange(moveToIndex(value, id, toIdx))}
          />
        ))}
      </Box>
      <FormHelperText sx={{ mt: 1 }}>
        Selecting a position reorders the list; each row has exactly one rank.
      </FormHelperText>
    </FormControl>
  );
}

/* --- numbered Question wrapper ------------------------------------------- */

function Question({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <FormControl fullWidth component="fieldset" sx={{ mb: 3 }}>
      <FormLabel sx={{ mb: 1, fontWeight: 700 }}>
        {label} {required && <span style={{ color: "red" }}>*</span>}
      </FormLabel>
      {children}
    </FormControl>
  );
}

/* --- page ----------------------------------------------------------------- */

export default function Page() {
  const { data: session, status } = useSession();

  const [formData, setFormData] = useState<FormData>({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
    isWAResident: false,

    pathway: "",
    highestEducation: "",
    currentlyEnrolledDegree: false,
    degreeCompletionWindow: "N/A",

    collegeName: "",
    degreeProgram: "",

    hasTrainingProgram: false,
    trainingProvider: "",

    hasCertifications: false,
    certifications: [],

    weekdayAvailabilityRank: [...WEEKDAYS],
    timeblockAvailabilityRank: [...TIMEBLOCKS],
  });

  const [successfullySubmitted, setSuccessfullySubmitted] = useState<boolean>();
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "success" | "error";
  }>({
    open: false,
    message: "",
    severity: "success",
  });

  useEffect(() => {
    if (status !== "authenticated") return;
    const u = session?.user as any;
    setFormData((prev) => ({
      ...prev,
      firstName: prev.firstName || u?.name?.split(" ")?.[0] || "",
      lastName: prev.lastName || u?.name?.split(" ")?.[1] || "",
      email: prev.email || u?.email || "",
    }));
  }, [status, session?.user]);

  const handleCertToggle = (cert: string) => {
    setFormData((prev) => {
      const set = new Set(prev.certifications);
      if (set.has(cert)) set.delete(cert);
      else set.add(cert);
      return { ...prev, certifications: Array.from(set) };
    });
  };

  const validate = (): string | null => {
    const r = formData;

    // residency rule
    if (!r.isWAResident) {
      return "Non-Washington residents are ineligible for the Career Prep program.";
    }

    const req = [
      ["firstName", r.firstName],
      ["lastName", r.lastName],
      ["email", r.email],
      ["phone", r.phone],
      ["pathway", r.pathway],
      ["highestEducation", r.highestEducation],
      ["degreeCompletionWindow", r.degreeCompletionWindow],
      ["collegeName", r.collegeName],
      ["degreeProgram", r.degreeProgram],
    ] as const;
    for (const [k, v] of req)
      if (!String(v || "").trim()) return `${k} is required`;
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(r.email))
      return "Invalid email address";
    if (r.hasTrainingProgram && !r.trainingProvider)
      return "Training provider is required";
    if (r.hasCertifications && r.certifications.length === 0)
      return "Select at least one certification";
    return null;
  };

  const toYesNo = (b: boolean) => (b ? "Yes" : "No");

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();

    const err = validate();
    if (err) {
      setSnackbar({ open: true, message: err, severity: "error" });
      return;
    }

    // Flat payload to Microsoft List (unchanged)
    const payload = {
      "First Name": formData.firstName.trim(),
      "Application Date": new Date().toISOString(),
      "Last Name": formData.lastName.trim(),
      "Email Address": formData.email.trim(),
      "Phone Number": formData.phone.trim(),

      Resident: toYesNo(formData.isWAResident),

      Pathways: formData.pathway,
      "Ed. Level": formData.highestEducation,

      "Tech Degree": formData.currentlyEnrolledDegree
        ? "Enrolled"
        : "Graduated",
      Enrolled: toYesNo(formData.currentlyEnrolledDegree),
      Graduated: toYesNo(!formData.currentlyEnrolledDegree),

      "Degree Program": formData.degreeProgram,
      "Expected Graduation": formData.currentlyEnrolledDegree
        ? formData.degreeCompletionWindow || ""
        : "N/A",
      College: formData.collegeName,

      "Tech Training Program": toYesNo(formData.hasTrainingProgram),
      "Training Provider": formData.hasTrainingProgram
        ? formData.trainingProvider || ""
        : "",

      "Obtained Certifications": toYesNo(formData.hasCertifications),
      Certifications: formData.hasCertifications
        ? formData.certifications.join(";")
        : "",

      "Day Availability": formData.weekdayAvailabilityRank.join(";"),
      "Time Availability": formData.timeblockAvailabilityRank.join(";"),
    } as const;

    try {
      const res = await fetch("/api/jobseekers/career-prep/apply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) throw new Error("Submission failed");

      setSuccessfullySubmitted(true);
      window.scrollTo({ top: 0, behavior: "instant" });
    } catch {
      setSuccessfullySubmitted(false);
      setSnackbar({
        open: true,
        message: "Submission failed. Please try again.",
        severity: "error",
      });
    }
  };

  const handleCloseSnackbar = () => setSnackbar((s) => ({ ...s, open: false }));

  return (
    <>
      {successfullySubmitted ? (
        <Box className="flex justify-center">
          <Box
            style={{ height: "100vh" }}
            className="profile-form-section main-content"
          >
            <Confetti />
            <h1>Next Steps</h1>
            <Typography sx={{ pt: 3, mb: 3 }}>
              You’re all set! Thanks for applying to Career Prep. CFA staff will
              be in contact with the next available enrollment date.
            </Typography>
            <PillButton href="/services/jobseekers/dashboard">
              Go to Dashboard
            </PillButton>
          </Box>
        </Box>
      ) : (
        <Paper elevation={0} sx={{ p: 3, maxWidth: "75%", mx: "auto", my: 4 }}>
          <Typography
            variant="h3"
            align="center"
            sx={{ fontWeight: 800, mb: 2 }}
          >
            Career Prep Application
          </Typography>

          <Typography sx={{ mb: 2 }}>
            Provided by Computing For All (CFA), Career Prep is a complimentary
            career readiness program that is designed to equip Washington State
            residents, who have recently completed or are nearing completion of
            a technology degree, with the essential skills to successfully enter
            the job market and initiate their tech career.
          </Typography>

          <Typography sx={{ mb: 1, fontWeight: 700 }}>Duration:</Typography>
          <Typography sx={{ mb: 2 }}>
            This program will run in 8 monthly cohorts beginning the first week
            of July 2025.
            <strong>
              {" "}
              CFA Staff will contact you with the next available start date.
            </strong>
          </Typography>

          <Typography sx={{ mb: 1, fontWeight: 700 }}>
            Eligibility Criteria:
          </Typography>
          <ul style={{ marginTop: 0, marginBottom: 16 }}>
            <li>Washington State resident</li>
            <li>
              Currently enrolled in or recently graduated from a tech degree
              program
            </li>
            <li>Actively seeking employment</li>
          </ul>

          <Typography sx={{ mb: 1, fontWeight: 700 }}>Benefits:</Typography>
          <ul style={{ marginTop: 0, marginBottom: 16 }}>
            <li>Career Readiness Support</li>
            <li>Networking Opportunities</li>
            <li>Job Placement Assistance</li>
          </ul>

          <Typography sx={{ mb: 1, fontWeight: 700 }}>Training:</Typography>
          <ul style={{ marginTop: 0, marginBottom: 16 }}>
            <li>
              <strong>5 Workshops:</strong>
              <ul
                style={{
                  marginTop: 8,
                  marginBottom: 8,
                  listStyleType: "disc",
                  paddingLeft: "20px",
                }}
              >
                <li>
                  Delivered weekly (two date &amp; time slots to accommodate
                  schedules)
                </li>
                <li>Building Your Brand</li>
                <li>Expanding Your Network</li>
                <li>Finding Opportunities</li>
                <li>Tailoring Your Application</li>
                <li>Interviewing Successfully</li>
              </ul>
            </li>
            <li>
              <strong>2 Weekly Office Hours (optional):</strong> Personalized
              support and feedback.
            </li>
            <li>
              <strong>Exit Interview:</strong> Meet with our Career Navigator
              for feedback and next steps.
            </li>
            <li>
              <strong>Job Search &amp; Job Placement Support:</strong> You’ll be
              added to the Job Placement Talent Pool upon completion.
            </li>
          </ul>

          {/* FORM ------------------------------------------------------------------ */}
          <form onSubmit={handleSubmit}>
            <Stack spacing={3} sx={{ py: 2 }}>
              {/* 1-4 Contact */}
              <Question label="First Name" required>
                <TextField
                  fullWidth
                  required
                  value={formData.firstName}
                  onChange={(e) =>
                    setFormData({ ...formData, firstName: e.target.value })
                  }
                />
              </Question>

              <Question label="Last Name" required>
                <TextField
                  fullWidth
                  required
                  value={formData.lastName}
                  onChange={(e) =>
                    setFormData({ ...formData, lastName: e.target.value })
                  }
                />
              </Question>

              <Question label="Email Address" required>
                <TextField
                  type="email"
                  fullWidth
                  required
                  value={formData.email}
                  onChange={(e) =>
                    setFormData({ ...formData, email: e.target.value })
                  }
                />
              </Question>

              <Question label="Phone Number" required>
                <TextField
                  fullWidth
                  required
                  value={formData.phone}
                  onChange={(e) =>
                    setFormData({ ...formData, phone: e.target.value })
                  }
                />
              </Question>

              {/* 5 Residency */}
              <Question label="Are you a Washington resident?" required>
                <RadioGroup
                  row
                  value={formData.isWAResident ? "Yes" : "No"}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      isWAResident: e.target.value === "Yes",
                    })
                  }
                >
                  <FormControlLabel
                    value="Yes"
                    control={<Radio />}
                    label="Yes"
                  />
                  <FormControlLabel value="No" control={<Radio />} label="No" />
                </RadioGroup>
              </Question>
              {formData.isWAResident && (
                <>
                  {/* 6 Pathway */}
                  <Question
                    label="What technical pathway are you most interested in?"
                    required
                  >
                    <Select
                      value={formData.pathway || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          pathway: e.target.value as string,
                        })
                      }
                      displayEmpty
                      fullWidth
                    >
                      <MenuItem value="" disabled>
                        Select pathway
                      </MenuItem>
                      {Object.values(CareerPrepPathways).map((p) => (
                        <MenuItem key={p} value={p}>
                          {p}
                        </MenuItem>
                      ))}
                    </Select>
                  </Question>

                  {/* 7 Highest Education */}
                  <Question
                    label="What is your highest level of education?"
                    required
                  >
                    <Select
                      value={formData.highestEducation || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          highestEducation: e.target.value as string,
                        })
                      }
                      displayEmpty
                      fullWidth
                    >
                      <MenuItem value="" disabled>
                        Select highest education
                      </MenuItem>
                      {Object.values(HighestCompletedEducationLevel).map(
                        (e) => (
                          <MenuItem key={e} value={e}>
                            {e}
                          </MenuItem>
                        ),
                      )}
                    </Select>
                  </Question>

                  {/* 8 Enrolled in Degree */}
                  <Question label="Are you currently enrolled in a technical degree program?">
                    <FormGroup>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.currentlyEnrolledDegree}
                            onChange={() => {
                              const newValue =
                                !formData.currentlyEnrolledDegree;
                              setFormData({
                                ...formData,
                                currentlyEnrolledDegree: newValue,
                                degreeCompletionWindow: newValue ? "" : "N/A", // enrolled -> empty; not enrolled -> N/A
                              });
                            }}
                          />
                        }
                        label="Yes"
                      />
                    </FormGroup>
                  </Question>

                  {/* 9 Degree Completion Window - conditional */}
                  {formData.currentlyEnrolledDegree && (
                    <Question
                      label="How many months are left until you graduate?"
                      required
                    >
                      <Select
                        value={formData.degreeCompletionWindow || ""} // empty until they choose
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            degreeCompletionWindow: e.target.value as string,
                          })
                        }
                        displayEmpty
                        fullWidth
                      >
                        <MenuItem value="" disabled>
                          Select timeframe
                        </MenuItem>
                        {DEGREE_WINDOW.map((w) => (
                          <MenuItem key={w} value={w}>
                            {w}
                          </MenuItem>
                        ))}
                      </Select>
                    </Question>
                  )}

                  {/* 10 College */}
                  <Question label="College (current/completed)" required>
                    <TextField
                      fullWidth
                      required
                      value={formData.collegeName}
                      onChange={(e: ChangeEvent<HTMLInputElement>) =>
                        setFormData({
                          ...formData,
                          collegeName: e.target.value,
                        })
                      }
                    />
                  </Question>

                  {/* 11 Technical Degree Program */}
                  <Question label="Technical degree program" required>
                    <Select
                      value={formData.degreeProgram || ""}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          degreeProgram: e.target.value as string,
                        })
                      }
                      displayEmpty
                      fullWidth
                    >
                      <MenuItem value="" disabled>
                        Select program
                      </MenuItem>
                      {DEGREE_PROGRAM_OPTIONS.map((opt) => (
                        <MenuItem key={opt} value={opt}>
                          {opt}
                        </MenuItem>
                      ))}
                    </Select>
                  </Question>

                  {/* 12 Training Program toggle */}
                  <Question label="I’m enrolled in or completed a technical training program">
                    <FormGroup>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.hasTrainingProgram}
                            onChange={() =>
                              setFormData({
                                ...formData,
                                hasTrainingProgram:
                                  !formData.hasTrainingProgram,
                                trainingProvider: !formData.hasTrainingProgram
                                  ? ""
                                  : formData.trainingProvider, // clear when unchecked
                              })
                            }
                          />
                        }
                        label="Yes"
                      />
                    </FormGroup>
                  </Question>

                  {/* 13 Training Provider (conditional dropdown) */}
                  {formData.hasTrainingProgram && (
                    <Question label="Training provider" required>
                      <Select
                        value={formData.trainingProvider || ""}
                        onChange={(e) =>
                          setFormData({
                            ...formData,
                            trainingProvider: e.target.value as string,
                          })
                        }
                        displayEmpty
                        fullWidth
                      >
                        <MenuItem value="" disabled>
                          Select provider
                        </MenuItem>
                        {TRAINING_PROVIDER_PROGRAMS.map((p) => (
                          <MenuItem key={p} value={p}>
                            {p}
                          </MenuItem>
                        ))}
                      </Select>
                    </Question>
                  )}

                  {/* 14 Certifications toggle */}
                  <Question label="I have technical certifications">
                    <FormGroup>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.hasCertifications}
                            onChange={() =>
                              setFormData({
                                ...formData,
                                hasCertifications: !formData.hasCertifications,
                                certifications: !formData.hasCertifications
                                  ? []
                                  : formData.certifications, // clear if unchecked
                              })
                            }
                          />
                        }
                        label="Yes"
                      />
                    </FormGroup>
                  </Question>

                  {/* 15 Certifications picker */}
                  {formData.hasCertifications && (
                    <Question label="Select certifications">
                      <FormHelperText sx={{ m: 0 }}>
                        Click to toggle
                      </FormHelperText>
                      <Box
                        sx={{
                          display: "flex",
                          flexWrap: "wrap",
                          gap: 1,
                          mt: 1,
                        }}
                      >
                        {CERTIFICATION_OPTIONS.map((c) => (
                          <Chip
                            key={c}
                            label={c}
                            variant={
                              formData.certifications.includes(c)
                                ? "filled"
                                : "outlined"
                            }
                            color={
                              formData.certifications.includes(c)
                                ? "primary"
                                : "default"
                            }
                            onClick={() => handleCertToggle(c)}
                          />
                        ))}
                      </Box>
                    </Question>
                  )}

                  {/* 16-17 Availability rankers */}
                  <Question label="Please rank the following week days in the order of your availability:">
                    <RankList
                      label=""
                      value={formData.weekdayAvailabilityRank}
                      onChange={(next) =>
                        setFormData((p) => ({
                          ...p,
                          weekdayAvailabilityRank: next,
                        }))
                      }
                    />
                  </Question>

                  <Question label="Please rank the following time blocks in the order of your availability:">
                    <RankList
                      label=""
                      value={formData.timeblockAvailabilityRank}
                      onChange={(next) =>
                        setFormData((p) => ({
                          ...p,
                          timeblockAvailabilityRank: next,
                        }))
                      }
                    />
                  </Question>
                </>
              )}
            </Stack>

            <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 2 }}>
              <PillButton type="submit">Submit Application</PillButton>
            </Box>
          </form>
        </Paper>
      )}

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </>
  );
}
