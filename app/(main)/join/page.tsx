"use client";
import React, { ChangeEvent, FormEvent, useState } from "react";
import {
  Typography,
  TextField,
  FormControlLabel,
  FormControl,
  FormLabel,
  Checkbox,
  Box,
  Container,
  Grid,
  FormGroup,
  Snackbar,
  Alert,
  AlertColor,
  RadioGroup,
  Radio,
} from "@mui/material";
import PillButton from "@/app/ui/components/PillButton";
import { JSX } from "react/jsx-runtime";

interface FormData {
  memberRole: string;
  firstName: string;
  lastName: string;
  jobTitle: string;
  organization: string;
  email: string;
  interests: string[];
}

interface SubmitStatus {
  open: boolean;
  severity: AlertColor;
  message: string;
}

interface PayloadData {
  "Member role": string;
  Firstname: string;
  Lastname: string;
  JobTitle: string;
  Organization: string;
  Email: string;
  "Area of Interest": string;
  "Form Name": string;
  Notification: string;
}

export default function Page(): JSX.Element {
  const [formData, setFormData] = useState<FormData>({
    memberRole: "",
    firstName: "",
    lastName: "",
    jobTitle: "",
    organization: "",
    email: "",
    interests: [],
  });

  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitStatus, setSubmitStatus] = useState<SubmitStatus>({
    open: false,
    severity: "success",
    message: "",
  });

  const memberRoles: string[] = [
    "Employers or Tech Industry Professionals",
    "Educators",
    "Community Organization/Nonprofit Professionals",
    "Workforce or Government Professionals",
  ];

  const interestOptions: string[] = [
    "Recruiting",
    "Employee skill development",
    "Tech curriculum improvement",
    "Internship programs",
    "Apprenticeship programs",
    "Career Launch programs",
    "Student job placement assistance",
    "Educational program support",
    "Other",
  ];

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();

    if (!formData.memberRole) {
      setSubmitStatus({
        open: true,
        severity: "error",
        message: "Please select a member type",
      });
      return;
    }

    setIsSubmitting(true);

    const payload: PayloadData = {
      "Member role": formData.memberRole,
      Firstname: formData.firstName,
      Lastname: formData.lastName,
      JobTitle: formData.jobTitle,
      Organization: formData.organization,
      Email: formData.email,
      "Area of Interest": formData.interests.join(", "),
      "Form Name": "Membership Form (universal) V4",
      Notification:
        "This is a notification that a contact form was submitted on your website (Washington Tech Workforce Coalition)",
    };

    try {
      const response = await fetch(
        "https://prod-25.westus.logic.azure.com:443/workflows/b1c10acdf2324ab097420749954854e9/triggers/manual/paths/invoke?api-version=2016-06-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=X297QuDQs7HctPalrTQIJ9Nh7-5TDUHhdnS51R1eb54",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        },
      );

      if (!response.ok) {
        throw new Error("Submission failed");
      }

      setSubmitStatus({
        open: true,
        severity: "success",
        message: "Form submitted successfully!",
      });

      setFormData({
        memberRole: "",
        firstName: "",
        lastName: "",
        jobTitle: "",
        organization: "",
        email: "",
        interests: [],
      });
    } catch (error) {
      console.error("Submission error:", error);
      setSubmitStatus({
        open: true,
        severity: "error",
        message: "Failed to submit form. Please try again.",
      });
    }

    setIsSubmitting(false);
  };

  const handleInterestToggle = (interest: string): void => {
    setFormData((prev) => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter((i) => i !== interest)
        : [...prev.interests, interest],
    }));
  };

  const handleCloseSnackbar = (): void => {
    setSubmitStatus((prev) => ({ ...prev, open: false }));
  };

  return (
    <>
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
          <Typography variant="h4" component="h1" align="center" gutterBottom>
            Join the Coalition
          </Typography>
          <Typography variant="subtitle1" align="center" sx={{ mb: 4 }}>
            Bridge skills gaps. Align curriculum with advances in technology.
            Expand employment opportunities.
          </Typography>
          <Typography variant="body1" sx={{ mb: 4 }}>
            Guided by AWS, Microsoft, Accenture, and WTIA, the Coalition creates
            a platform ​for the state’s postsecondary education and training
            institutions to address industry priorities.
          </Typography>
          <Typography variant="body1" sx={{ mb: 4 }}>
            <strong>Employers: Access unique sources of quality talent.</strong>
            Tap into talent pools that are not easily accessible​ in traditional
            job boards. You’ll have direct access to quality candidates in
            Software Development, Cybersecurity, IT/Cloud Support, Data
            Analytics, and Data Center Support.​ The Industry Committee meets
            quarterly in January, April, July, and October, and with the full
            Coalition twice a year.
          </Typography>
          <Typography variant="body1" sx={{ mb: 4 }}>
            <strong>Educators: Align curriculum, get students hired.</strong>
            Align curriculum with advances in technology through direct inputs
            from industry leaders. Leverage the Coalition to build employer
            relationships that support student placements. The Education
            Committee meets quarterly in February. May, August, and November,
            and with the full Coalition twice a year.
          </Typography>
          <Typography variant="body1" sx={{ mb: 4 }}>
            <strong>Community Partners: Drive economic development.</strong>
            Identify opportunities for public sector and non-Tech employers to
            access channels into education and employment for constituent
            populations. help your employer stakeholders avoid the avalanche of
            resumes from big job boards and receive vetted candidates from
            trusted sources. join the Coalition meetings twice a year.
          </Typography>
          <Typography variant="body1" sx={{ mb: 4 }}>
            Please join the Coalition by completing this form.
          </Typography>
          <FormControl fullWidth required sx={{ mb: 4 }}>
            <FormLabel>
              I would like to receive information relevant to:
            </FormLabel>
            <RadioGroup
              name="memberRole"
              value={formData.memberRole}
              onChange={(e) =>
                setFormData((prev) => ({ ...prev, memberRole: e.target.value }))
              }
            >
              {memberRoles.map((type) => (
                <FormControlLabel
                  key={type}
                  value={type}
                  control={<Radio />}
                  label={type}
                />
              ))}
            </RadioGroup>
          </FormControl>

          <Grid container spacing={2} sx={{ mb: 4 }}>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                required
                fullWidth
                label="First Name"
                value={formData.firstName}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, firstName: e.target.value })
                }
              />
            </Grid>
            <Grid size={{ xs: 12, sm: 6 }}>
              <TextField
                required
                fullWidth
                label="Last Name"
                value={formData.lastName}
                onChange={(e: ChangeEvent<HTMLInputElement>) =>
                  setFormData({ ...formData, lastName: e.target.value })
                }
              />
            </Grid>
          </Grid>

          <TextField
            fullWidth
            label="Job Title"
            value={formData.jobTitle}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setFormData({ ...formData, jobTitle: e.target.value })
            }
            sx={{ mb: 4 }}
          />

          <TextField
            required
            fullWidth
            label="Organization Name"
            value={formData.organization}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setFormData({ ...formData, organization: e.target.value })
            }
            sx={{ mb: 4 }}
          />

          <TextField
            required
            fullWidth
            label="Email"
            type="email"
            value={formData.email}
            onChange={(e: ChangeEvent<HTMLInputElement>) =>
              setFormData({ ...formData, email: e.target.value })
            }
            sx={{ mb: 4 }}
          />

          <FormControl component="fieldset" fullWidth sx={{ mb: 4 }}>
            <FormLabel component="legend">I am interested in:</FormLabel>
            <FormGroup>
              {interestOptions.map((interest) => (
                <FormControlLabel
                  key={interest}
                  control={
                    <Checkbox
                      checked={formData.interests.includes(interest)}
                      onChange={() => handleInterestToggle(interest)}
                    />
                  }
                  label={interest}
                />
              ))}
            </FormGroup>
          </FormControl>

          <PillButton type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Submitting..." : "Submit"}
          </PillButton>
        </Box>

        <Snackbar
          open={submitStatus.open}
          autoHideDuration={6000}
          onClose={handleCloseSnackbar}
          anchorOrigin={{ vertical: "top", horizontal: "center" }}
        >
          <Alert
            onClose={handleCloseSnackbar}
            severity={submitStatus.severity}
            sx={{ width: "100%" }}
          >
            {submitStatus.message}
          </Alert>
        </Snackbar>
      </Container>
    </>
  );
}
