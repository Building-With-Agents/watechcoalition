import * as React from "react";
import Box from "@mui/material/Box";
import Rating from "@mui/material/Rating";
import StarIcon from "@mui/icons-material/Star";

const labels: { [index: string]: string } = {
  1: "Not Proficient",
  2: "Novice",
  3: "Beginner",
  4: "Competent",
  5: "Proficient",
};

export default function LikertRating({ value }: { value: number }) {
  return (
    <Box sx={{ width: 200, display: "flex", alignItems: "center" }}>
      <Rating
        name="text-feedback"
        value={value}
        readOnly
        precision={1}
        emptyIcon={<StarIcon style={{ opacity: 0.55 }} fontSize="inherit" />}
      />
      <Box sx={{ ml: 2 }}>{labels[value]}</Box>
    </Box>
  );
}
