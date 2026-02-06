"use client";

import React from "react";
import { Typography, Box } from "@mui/material";

export default function BookAppointmentPage() {
  return (
    <Box sx={{ mb: 4, mx: { xs: 1, md: 6.25 } }}>
      <Box>
        <Typography variant="h4">Application Submitted!</Typography>
        <Typography gutterBottom>
          Thank you for applying. Please schedule a brief meeting with our
          Career Services team using the calendar below:
        </Typography>
      </Box>
      <Box
        sx={{
          height: "75vh",
          width: "100%",
          borderTop: "1px solid",
          borderColor: "divider",
        }}
      >
        <iframe
          src="https://outlook.office.com/owa/calendar/CFACareerServices@computingforall.org/bookings/?ismsaljsauthenabled"
          width="100%"
          height="100%"
          style={{
            border: 0,
            display: "block",
          }}
          title="Schedule a Meeting with CFA Career Services"
        ></iframe>
      </Box>
    </Box>
  );
}
