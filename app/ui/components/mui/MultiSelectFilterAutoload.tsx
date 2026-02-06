"use client";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import ListItemText from "@mui/material/ListItemText";
import Select, { SelectChangeEvent } from "@mui/material/Select";
import Checkbox from "@mui/material/Checkbox";
import React from "react";

interface Props<ValueType> {
  id: string;
  apiAutoloadRoute: string;
  label: string;
  value: string[];
  onChange: (event: SelectChangeEvent<string[]>) => void;
  getOptionLabel: (option: ValueType) => string;
  [key: string]: any;
}

export default function MultipleSelectFilterAutoload<ValueType>({
  apiAutoloadRoute,
  label,
  value,
  onChange,
  getOptionLabel,
  ...rest
}: Props<ValueType>) {
  const [options, setOptions] = React.useState<ValueType[]>([]);
  const [loading, setLoading] = React.useState(false);
  const formattedLabel = `${label} (${value.length})`;

  React.useEffect(() => {
    const abortController = new AbortController();

    const loadOptions = async () => {
      try {
        setLoading(true);
        const response = await fetch(apiAutoloadRoute, {
          signal: abortController.signal,
        });

        if (!response.ok) throw new Error("Fetch failed");

        const data: ValueType[] = await response.json();
        if (!abortController.signal.aborted) {
          setOptions(data);
        }
      } catch (error) {
        if (!abortController.signal.aborted) {
          console.error("Fetch error:", error);
        }
      } finally {
        if (!abortController.signal.aborted) {
          setLoading(false);
        }
      }
    };

    loadOptions();

    return () => {
      abortController.abort();
    };
  }, [apiAutoloadRoute]);

  return (
    <FormControl fullWidth>
      <InputLabel>{formattedLabel}</InputLabel>
      <Select
        multiple
        value={value}
        onChange={onChange}
        input={<OutlinedInput />}
        disabled={loading}
        renderValue={(selected) => selected.join(", ")}
        {...rest}
      >
        {options.map((option) => {
          const optionLabel = getOptionLabel(option);
          return (
            <MenuItem dense={true} key={optionLabel} value={optionLabel}>
              <Checkbox checked={value.includes(optionLabel)} />
              <ListItemText primary={optionLabel} />
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  );
}
