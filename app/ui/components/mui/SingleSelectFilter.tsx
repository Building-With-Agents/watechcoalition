import * as React from "react";
import OutlinedInput from "@mui/material/OutlinedInput";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import FormControl from "@mui/material/FormControl";
import ListItemText from "@mui/material/ListItemText";
import Select, { SelectChangeEvent } from "@mui/material/Select";

interface Props {
  id?: string;
  options: { label: string; value: string }[];
  label: string;
  value: string[];
  onChange: (event: SelectChangeEvent<string[]>) => void;
}

export default function SingleSelectCheckmarks({
  id,
  options,
  label,
  value,
  onChange,
}: Props) {
  const [filter, setFilter] = React.useState<string[]>([]);
  // const [formattedLabel, setFormattedLabel] = React.useState<string>(label);

  const handleChange = (event: SelectChangeEvent<string[]>) => {
    const {
      target: { value },
    } = event;

    setFilter(typeof value === "string" ? value.split(",") : value);
    onChange(event);
  };

  // Load the initial filter values
  React.useEffect(() => {
    if (value?.length > 0) setFilter(value);
  }, []);

  return (
    <FormControl fullWidth>
      <InputLabel>{label}</InputLabel>
      <Select
        id={id}
        className=""
        value={filter}
        onChange={handleChange}
        input={<OutlinedInput />}
      >
        {options.map((option) => (
          <MenuItem key={option.label} value={option.value}>
            <ListItemText primary={option.label} />
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}
