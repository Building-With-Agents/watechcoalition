"use client";

import { Snackbar, SnackbarContent, IconButton } from "@mui/material";
import {
  Close as CloseIcon,
  CheckCircleOutline as CheckCircleOutlineIcon,
  ErrorOutline as ErrorOutlineIcon,
} from "@mui/icons-material";

interface SnackbarWithIconProps {
  open: boolean;
  onClose: (event?: React.SyntheticEvent | Event, reason?: string) => void;
  variant: "success" | "alert";
  message: React.ReactNode;
  autoHideDuration?: number;
  anchorOrigin?: {
    vertical: "top" | "bottom";
    horizontal: "left" | "center" | "right";
  };
}

const SnackbarWithIcon: React.FC<SnackbarWithIconProps> = ({
  open,
  onClose,
  message,
  variant,
  autoHideDuration = 6000,
  anchorOrigin = { vertical: "top", horizontal: "center" },
}) => {
  const icon =
    variant === "success" ? <CheckCircleOutlineIcon /> : <ErrorOutlineIcon />;
  const backgroundColor = variant === "success" ? "#2E7D32" : "#D32F2F";
  return (
    <Snackbar
      open={open}
      autoHideDuration={autoHideDuration}
      onClose={onClose}
      anchorOrigin={anchorOrigin}
      sx={{
        width: "100%",
        maxWidth: "48rem", // max-w-3xl equivalent
      }}
    >
      <SnackbarContent
        sx={{
          backgroundColor,
          width: "100%",
          boxSizing: "border-box",
          padding: "16px",
          display: "flex",
          alignItems: "center",
          position: "relative",
        }}
        message={
          <div className="snackbar-message">
            {icon}
            <div>{message}</div>
          </div>
        }
        action={
          <IconButton
            size="small"
            aria-label="close"
            color="inherit"
            onClick={onClose}
            sx={{ position: "absolute", top: 8, right: 8 }}
          >
            <CloseIcon />
          </IconButton>
        }
      />
    </Snackbar>
  );
};

export default SnackbarWithIcon;
