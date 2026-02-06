import React, { ChangeEvent, useState } from "react";
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
} from "@mui/material";

interface Props {
  children: React.ReactNode;
  id: string;
  options: { label: string; value: string }[];
  className?: string;
  placeholder?: string;
  required?: boolean;
  onChange?: (event: ChangeEvent<HTMLSelectElement>) => void;
  disabled?: boolean;
  value?: string;
  defaultValue?: string;
}

export default function SelectOptionsWithLabel({
  children,
  id,
  options,
  className = "",
  placeholder = "",
  required = false,
  onChange,
  value,
  defaultValue,
  disabled = false,
}: Props) {
  const [internalValue, setInternalValue] = useState("");
  const labelId = `${id}-label`;

  const handleChange = (event: SelectChangeEvent<string>) => {
    if (onChange) {
      const syntheticEvent = {
        ...event,
        target: {
          ...event.target,
          name: id,
          value: event.target.value,
        },
      } as unknown as ChangeEvent<HTMLSelectElement>;

      onChange(syntheticEvent);
    } else {
      setInternalValue(event.target.value);
    }
  };

  return (
    <FormControl
      className={className}
      fullWidth
      disabled={disabled}
      required={required}
      sx={{ position: "relative" }}
    >
      <InputLabel
        id={labelId}
        sx={{
          backgroundColor: "background.paper",
          px: 1,
          left: "-3px",
          transform: "translate(14px, -9px) scale(0.75)",
          "&.Mui-focused": {
            color: "primary.main",
          },
        }}
      >
        {children}
      </InputLabel>

      <Select
        name={id}
        labelId={labelId}
        id={id}
        value={value ?? internalValue}
        defaultValue={defaultValue}
        onChange={handleChange}
        displayEmpty={!!placeholder}
        renderValue={(selected) => selected || placeholder}
      >
        {placeholder && (
          <MenuItem value="" disabled>
            {placeholder}
          </MenuItem>
        )}
        {options.map((item) => (
          <MenuItem key={`${id}-option-${item.value}`} value={item.value}>
            {item.label}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
