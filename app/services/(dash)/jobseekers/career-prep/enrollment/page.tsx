"use client";
import {
  Alert,
  Box,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  FormLabel,
  Grid,
  Link,
  List,
  ListItem,
  ListItemText,
  Paper,
  Snackbar,
  TextField,
  Typography,
} from "@mui/material";
import PillButton from "@/app/ui/components/PillButton";
import { useSession } from "next-auth/react";
import React, { ChangeEvent, useEffect, useState } from "react";
import NextLink from "next/link";
import Confetti from "@/app/ui/components/Confetti";
import "@/app/ui/profile-creation.css";

interface FormData {
  streetAddress: string;
  priorityPopulations: string[];
}

export default function Page() {
  const { data: session, status } = useSession();
  const [formData, setFormData] = useState<FormData>({
    streetAddress: "",
    priorityPopulations: [],
  });
  const [successfullySubmitted, setSuccessfullySubmitted] = useState<boolean>();
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: "success" | "error";
  }>({ open: false, message: "", severity: "success" });

  const priorityPopulations: string[] = [
    "COVID-impacted workers",
    "Underemployed individuals",
    "Long-term unemployed individuals",
    "Short-term unemployed individuals",
    "Incumbent workers",
    "People living in rural communities",
    "People living in coal communities",
    "Military spouses",
    "Disconnected youth",
    "Individuals in substance abuse recovery",
    "Individuals participating in TANF, SNAP, WIC",
    "Individuals with past criminal records (e.g., justice impacted, reentry participants)",
    "Prefer not to answer",
  ];

  useEffect(() => {
    const initializeFormFields = async () => {
      if (!session?.user.id) return;
      if (status === "authenticated") {
        const { jobseekerId } = session.user;
        try {
          if (!jobseekerId) return;
        } catch (error) {
          console.error(error);
        }
      }
    };
    initializeFormFields();
  }, [session?.user?.id]);

  const handlePrioritySelect = (type: string): void => {
    setFormData((prev) => ({
      ...prev,
      priorityPopulations: prev.priorityPopulations.includes(type)
        ? prev.priorityPopulations.filter((t) => t !== type)
        : [...prev.priorityPopulations, type],
    }));
  };

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    e.preventDefault();
    if (!formData.streetAddress) {
      alert("Street Address is required.");
      return;
    }
    if (formData.priorityPopulations.length === 0) {
      alert("Please select at least one priority population.");
      return;
    }

    const payload = {
      streetAddress: formData.streetAddress,
      priorityPopulations: formData.priorityPopulations.join("~"),
    };
    const response = await fetch(
      "/api/jobseekers/career-prep/enrollment/submit/",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      },
    );
    if (response.ok) {
      setSuccessfullySubmitted(true);
      window.scrollTo({ top: 0, behavior: "instant" });
    } else {
      setSuccessfullySubmitted(false);
      setSnackbar({
        open: true,
        message: "Submission failed. Please try again.",
        severity: "error",
      });
    }
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  return (
    <>
      {successfullySubmitted ? (
        <>
          <Box className="flex justify-center">
            <Box
              style={{ height: "100vh" }}
              className="profile-form-section main-content"
            >
              <Confetti />
              <h1>Next Steps</h1>
              <Typography sx={{ pt: 3, mb: 3 }}>
                {
                  "You’re officially enrolled! We're excited to officially welcome you to Career Prep. Return to your dashboard to view your personalized development plan and access the Canvas training."
                }
              </Typography>
              {/*<p className="subtitle-congrats">{`Thank you again for your participation!`}</p>*/}
              <Grid container>
                <PillButton href="/services/jobseekers/dashboard">
                  Go to Dashboard
                </PillButton>
              </Grid>
            </Box>
          </Box>
        </>
      ) : (
        <Paper elevation={0} sx={{ p: 3, maxWidth: "75%", mx: "auto", my: 4 }}>
          <Typography variant="h4" align="center" sx={{ mb: 4 }}>
            Career Prep Enrollment Form
          </Typography>
          <Typography>
            As a Washington Jobs Initiative (WJI) program provider partnered
            with the Washington Tech Workforce Coalition (WTWC) and funded by
            the Good Jobs Challenge (GJC) Grant, Computing For All&apos;s Career
            Prep training program prioritizes individuals and communities kept
            furthest from opportunity. This includes but is not limited to:
          </Typography>
          <List
            sx={{
              listStyleType: "disc",
              "& .MuiListItem-root": { display: "list-item", marginLeft: 3 },
            }}
          >
            <ListItem disablePadding>
              <ListItemText>Women</ListItemText>
            </ListItem>
            <ListItem disablePadding>
              <ListItemText>
                Black, Latinx, Indigenous and Native American, Asian American,
                and Pacific Islander individuals
              </ListItemText>
            </ListItem>
            <ListItem disablePadding>
              <ListItemText>LGBTQIA2S+ individuals</ListItemText>
            </ListItem>
            <ListItem disablePadding>
              <ListItemText>Individuals with disabilities</ListItemText>
            </ListItem>
            <ListItem disablePadding>
              <ListItemText>Low-income individuals</ListItemText>
            </ListItem>
            <ListItem disablePadding>
              <ListItemText>
                Residents of underserved communities (e.g., Tribal Lands,
                Persistent Poverty Counties, rural areas)
              </ListItemText>
            </ListItem>
          </List>
          <Typography sx={{ mb: 1 }}>
            To comply with grant requirements and ensure program effectiveness,
            we are collecting data on participant demographics. Your personal
            information is confidential and will be used solely for grant
            reporting purposes.
          </Typography>
          <Typography>
            For more information about the WJI and GJC Grant, visit:
          </Typography>
          <Link
            component={NextLink}
            target="_blank"
            href={
              "https://wsac.wa.gov/sites/default/files/Washington-Student-Achievement-Project-Narrative.pdf"
            }
          >
            https://wsac.wa.gov/sites/default/files/Washington-Student-Achievement-Project-Narrative.pdf
          </Link>

          <form onSubmit={handleSubmit}>
            <Box sx={{ py: 2 }}>
              <Grid container>
                <Grid size={12}>
                  <Box sx={{ maxWidth: "720px" }}>
                    <FormControl
                      fullWidth
                      required
                      component="fieldset"
                      sx={{ mb: 2 }}
                    >
                      <FormLabel>What is your Street Address?</FormLabel>
                      <TextField
                        fullWidth
                        id="streetAddress"
                        name="streetAddress"
                        value={formData?.streetAddress}
                        onChange={(e: ChangeEvent<HTMLInputElement>) =>
                          setFormData({
                            ...formData,
                            streetAddress: e.target.value,
                          })
                        }
                      />
                    </FormControl>
                  </Box>
                </Grid>
                <Grid size={12}>
                  <FormControl required component="fieldset" sx={{ mb: 2 }}>
                    <FormLabel component="legend">
                      Please indicate if you identify with any of the following
                      priority populations:
                    </FormLabel>
                    <FormHelperText sx={{ m: 0 }}>
                      Select all that apply
                    </FormHelperText>
                    <FormGroup>
                      {priorityPopulations.map((type) => (
                        <FormControlLabel
                          key={type}
                          control={
                            <Checkbox
                              checked={formData?.priorityPopulations.includes(
                                type,
                              )}
                              onChange={() => handlePrioritySelect(type)}
                            />
                          }
                          label={type}
                        />
                      ))}
                    </FormGroup>
                  </FormControl>
                </Grid>
              </Grid>
            </Box>
            <Box
              sx={{ display: "flex", justifyContent: "space-between", mt: 4 }}
            >
              <Box></Box>
              <PillButton type="submit">Submit</PillButton>
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
