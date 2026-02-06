"use client";

import * as React from "react";
import Button from "@mui/material/Button";
import Popover from "@mui/material/Popover";
import TextField from "@mui/material/TextField";
import { Box } from "@mui/material";

export default function ShareMenu({
  href,
  children,
}: {
  href: string;
  children: React.ReactNode;
}) {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [isCopied, setIsCopied] = React.useState(false);
  const open = Boolean(anchorEl);
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    if (isCopied) setIsCopied(false);
  };
  const handleFocus = (event: { target: { select: () => any } }) =>
    event.target.select();
  const handleClose = () => {
    setAnchorEl(null);
  };

  let url = "";
  if (typeof window !== "undefined") {
    url = window.location.protocol + "//" + window.location.hostname;
    if (window.location.port != "") url += ":" + window.location.port;
    url += href;
  }

  function copyLink() {
    navigator.clipboard.writeText(url);
    setIsCopied(true);
  }

  return (
    <div>
      <div onClick={handleClick}>{children}</div>
      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: "bottom",
          horizontal: "left",
        }}
      >
        <Box sx={{ p: 1.5 }}>
          <TextField
            hiddenLabel
            size="small"
            id="filled-hidden-label-outlined-read-only-input"
            defaultValue={url}
            slotProps={{
              input: {
                readOnly: true,
              },
            }}
            onFocus={handleFocus}
          />
        </Box>
        <Button fullWidth variant="text" onClick={copyLink}>
          {isCopied ? "Link Copied!" : "Copy Link"}
        </Button>
      </Popover>
    </div>
  );
}
