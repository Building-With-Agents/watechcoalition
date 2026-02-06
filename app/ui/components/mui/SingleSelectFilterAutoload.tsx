"use client";
import React from "react";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import ListItemText from "@mui/material/ListItemText";
import Select, { SelectChangeEvent } from "@mui/material/Select";

interface Props<ValueType> {
  apiAutoloadRoute: string;
  label: string;
  value: string;
  onChange: (event: SelectChangeEvent<string>) => void;
  getOptionLabel: (option: ValueType) => string;
  getOptionValue?: (value: ValueType) => string;
  [key: string]: any;
}

export default function SingleSelectFilterAutoload<ValueType>({
  apiAutoloadRoute,
  label,
  value,
  onChange,
  getOptionLabel,
  getOptionValue,
  ...rest
}: Props<ValueType>) {
  const [options, setOptions] = React.useState<ValueType[]>([]);
  const [loading, setLoading] = React.useState(false);
  const abortControllerRef = React.useRef<AbortController>(null);

  React.useEffect(() => {
    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const autoload = async () => {
      try {
        setLoading(true);
        const response = await fetch(apiAutoloadRoute, {
          signal: controller.signal,
        });
        const data: ValueType[] = await response.json();
        setOptions(data);
      } catch (error) {
        if (!controller.signal.aborted) {
          console.error("Error fetching data:", error);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    };
    autoload();
    return () => controller.abort();
  }, [apiAutoloadRoute]);

  return (
    <FormControl fullWidth>
      <InputLabel>{label}</InputLabel>
      <Select
        value={value}
        disabled={loading}
        onChange={onChange}
        input={<OutlinedInput />}
        {...rest}
      >
        <MenuItem dense={true} value="">
          <ListItemText primary="Any" />
        </MenuItem>
        {options.map((option) => {
          const optionLabel = getOptionLabel(option);
          let optionValue;
          if (getOptionValue) optionValue = getOptionValue(option);
          return (
            <MenuItem
              dense={true}
              key={optionLabel}
              value={optionValue ? optionValue : optionLabel}
            >
              {optionLabel}
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  );
}
