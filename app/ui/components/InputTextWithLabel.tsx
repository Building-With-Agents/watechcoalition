"use client";

import { TextField } from "@mui/material";
import { useState } from "react";

interface Props {
  children: React.ReactNode;
  id: string;
  disabled?: boolean;
  className?: string;
  onChange?: React.ChangeEventHandler<HTMLInputElement>;
  value?: string;
  defaultValue?: string;
  [key: string]: any;
}

export default function InputTextWithLabel({
  children,
  id,
  disabled = false,
  className = "",
  onChange,
  value,
  defaultValue,
  ...rest
}: Props) {
  const [internalValue, setInternalValue] = useState(defaultValue || "");

  const handleChange: React.ChangeEventHandler<HTMLInputElement> = (e) => {
    if (onChange) {
      onChange(e);
    } else {
      setInternalValue(e.target.value);
    }
  };

  return (
    <TextField
      id={id}
      name={id}
      label={children}
      fullWidth
      disabled={disabled}
      className={className}
      value={value ?? internalValue}
      defaultValue={defaultValue}
      onChange={handleChange}
      {...rest}
    />
  );
}
