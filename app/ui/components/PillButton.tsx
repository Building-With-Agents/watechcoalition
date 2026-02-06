import React from "react";
import { Button, ButtonProps } from "@mui/material";

interface PillButtonProps extends ButtonProps {
  target?: string;
  href?: string;
}

const PillButton: React.FC<PillButtonProps> = ({
  target,
  href,
  sx,
  variant = "contained",
  color = "primary",
  ...props
}) => {
  return (
    <Button
      disableElevation
      variant={variant}
      component={href ? "a" : "button"}
      href={href || undefined}
      target={target}
      color={color}
      sx={{
        borderRadius: "9999px",
        textTransform: "none",
        fontWeight: 500,
        transition: "all 0.3s ease-in-out",
        padding: "0.5rem 1.25rem",
        ...(variant === "contained" &&
          color === "inherit" && {
            backgroundColor: "neutral.100",
            "&:hover": {
              backgroundColor: "neutral.200",
            },
          }),
        ...sx,
      }}
      {...props}
    />
  );
};

export default PillButton;
