import { LinearProgress } from "@mui/material";
interface Props {
  progress: number;
}

export default function ProgressBarFlat({ progress }: Props) {
  return (
    <>
      <LinearProgress
        variant="determinate"
        value={progress}
        sx={{
          height: 8,
          bgcolor: "#EEEEEE",
          "& .MuiLinearProgress-bar": {
            backgroundColor: "#0891B2",
          },
        }}
      />{" "}
    </>
  );
}
