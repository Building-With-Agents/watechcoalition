import { useEffect, useRef } from "react";
import { Tooltip } from "@mui/material";
import { useTheme } from "@mui/material/styles";

interface Props {
  open: boolean;
  errorMessage: string;
  children: React.ReactElement<unknown, any>;
  placement?:
    | "bottom-start"
    | "bottom-end"
    | "bottom"
    | "left-end"
    | "left-start"
    | "left"
    | "right-end"
    | "right-start"
    | "right"
    | "top-end"
    | "top-start"
    | "top"
    | undefined;
}

export default function RequiredTooltip({
  open,
  errorMessage,
  children,
  placement = "top-start",
  ...rest
}: Props) {
  const theme = useTheme();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (open) {
      if (ref?.current) {
        const topOffset =
          window.scrollY + ref.current.getBoundingClientRect().top - 45;
        window.scrollTo({
          top: topOffset,
          behavior: "smooth",
        });
      }
    }
  }, [open]);

  return (
    <Tooltip
      open={open}
      title={errorMessage}
      placement={placement}
      arrow
      slotProps={{
        tooltip: {
          sx: {
            backgroundColor: theme.palette.error.main,
            color: theme.palette.error.contrastText,
          },
        },
        arrow: {
          sx: {
            color: theme.palette.error.main,
          },
        },
      }}
      {...rest}
    >
      <div ref={ref}>{children}</div>
    </Tooltip>
  );
}
