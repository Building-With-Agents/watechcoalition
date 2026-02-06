"use client";
import * as React from "react";
import Box from "@mui/material/Box";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import Select, { SelectChangeEvent } from "@mui/material/Select";

export default function ScreenedDropdown(props: {
  screened: boolean;
  jobseekerId: string;
}) {
  const [screened, setScreened] = React.useState(props.screened ? "yes" : "no");

  const handleChange = async (event: SelectChangeEvent) => {
    const newValue = event.target.value as string;
    setScreened(newValue);
    try {
      const response = await fetch("/api/admin/career-prep/screening-status", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          jobseekerId: props.jobseekerId,
          prescreened: newValue === "yes",
        }),
      });

      if (!response.ok) {
        alert("Failed to update screening status, please try again later");
      }
    } catch (error) {
      console.error("Error updating screening status:", error);
    }
  };

  return (
    <Box
      sx={{
        width: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        height: "100%", // Ensures vertical alignment in the cell
      }}
    >
      <FormControl sx={{ minWidth: 120 }} size="small">
        <Select
          id={`showcase-select-${props.jobseekerId}`}
          value={screened}
          onChange={handleChange}
        >
          <MenuItem value={"yes"}>Yes</MenuItem>
          <MenuItem value={"no"}>No</MenuItem>
        </Select>
      </FormControl>
    </Box>
  );
}
