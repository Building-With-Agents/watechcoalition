import React from "react";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import ListItemText from "@mui/material/ListItemText";
import Select, { SelectChangeEvent } from "@mui/material/Select";
import Checkbox from "@mui/material/Checkbox";
import { useMemo } from "react";

interface Props {
  options: { label: string; value: string }[];
  label: string;
  value: string[];
  onChange: (event: SelectChangeEvent<string[]>) => void;
}

function MultipleSelectCheckmarksComponent({
  options,
  label,
  value,
  onChange,
}: Props) {
  const selectedValues = useMemo(() => new Set(value), [value]);
  const formattedLabel = `${label} (${value.length})`;

  return (
    <FormControl fullWidth>
      <InputLabel>{formattedLabel}</InputLabel>
      <Select
        multiple
        value={value}
        onChange={onChange}
        input={<OutlinedInput label={formattedLabel} />}
        renderValue={(selected) => selected.join(", ")}
      >
        {options.map((option) => (
          <MenuItem key={option.value} value={option.value}>
            <Checkbox checked={selectedValues.has(option.value)} />
            <ListItemText primary={option.label} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

export const MultipleSelectCheckmarks = React.memo(
  MultipleSelectCheckmarksComponent,
);
