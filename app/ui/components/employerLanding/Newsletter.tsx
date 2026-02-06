"use client";
import { Button, Grid, Stack, Typography } from "@mui/material";
import { useState } from "react";

export default function Newsletter() {
  const placeholderText = "johnsmith@gmail.com";
  const [value, setValue] = useState("");

  return (
    <Stack sx={{ my: 7.5, px: { xs: 2, sm: 3 } }}>
      <Typography
        variant="h1"
        color="secondary"
        sx={{ fontWeight: 500, mb: 0.625, textAlign: "center" }}
      >
        Stay Connected
      </Typography>
      <Typography
        variant="h2"
        color="textDisabled"
        sx={{
          fontWeight: 500,
          mb: 6.25,
          textAlign: "center",
        }}
      >
        Get event invites & personalized updates.
      </Typography>
      <Stack
        container
        component={Grid}
        sx={{ justifyContent: "center", alignItems: "center" }}
      >
        <Grid size={6}>
          <input
            type="email"
            placeholder={placeholderText}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            style={{
              width: "100%",
              height: "56px",
              padding: "18px 22px",
              marginBottom: "20px",
              borderRadius: "28px",
              border: "none",
              outline: "none",
              background: "#f6f6f6",
              color: value ? "#333333" : "#b3b3b3",
              fontSize: "20px",
              fontWeight: 600,
              boxSizing: "border-box",
              display: "block",
              WebkitAppearance: "none",
              MozAppearance: "none",
            }}
          />
        </Grid>
        <Grid size={6}>
          <Button
            fullWidth
            size="large"
            variant="contained"
            sx={{ borderRadius: "25px" }}
          >
            Submit
          </Button>
        </Grid>
      </Stack>
    </Stack>
  );
}
