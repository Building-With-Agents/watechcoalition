import { TextField } from "@mui/material";
import { ChangeEventHandler } from "react";

interface Props {
  id: string;
  label: string;
  onChange?:
    | ChangeEventHandler<HTMLInputElement | HTMLTextAreaElement>
    | undefined;
  placeholder?: string | undefined;
  [key: string]: any;
}

export default function TextFieldWithSeparatedLabel({
  id,
  label,
  onChange,
  placeholder,
  ...rest
}: Props) {
  return (
    <TextField
      {...rest}
      id={id}
      label={label}
      placeholder={placeholder}
      margin="normal"
      size="medium"
      variant="outlined"
      onChange={onChange}
      InputLabelProps={{
        sx: {
          color: "black",
          marginTop: -4,
          pointerEvents: "auto",
          transform: "scale(1.0)",
        },
      }}
      InputProps={{
        notched: false,
      }}
      sx={{
        marginTop: 4,
        "& .MuiOutlinedInput-root input:focus": {
          boxShadow: "none",
        },
        "& .MuiInputBase-root.MuiOutlinedInput-root .MuiInputBase-input.MuiOutlinedInput-input::placeholder":
          {
            opacity: "0.42!important",
          },
        "& .MuiOutlinedInput-root .MuiOutlinedInput-notchedOutline legend": {
          display: "none",
        },
      }}
    />
  );
}
