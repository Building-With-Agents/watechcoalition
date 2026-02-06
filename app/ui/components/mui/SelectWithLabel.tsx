import {
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import { ReactNode } from "react";

interface Props {
  id: string;
  options: { label: string; value: string }[];
  label?: string | undefined;
  value?: string | undefined;
  onChange?:
    | ((event: SelectChangeEvent<string>, child: ReactNode) => void)
    | undefined;
  [key: string]: any;
}

export default function SelectWithLabel({
  id,
  options,
  label,
  value,
  onChange,
  ...rest
}: Props) {
  return (
    <FormControl fullWidth>
      <InputLabel id={id + "-label"}>{label}</InputLabel>
      <Select
        labelId={id + "-label"}
        id={id}
        value={value}
        label={label}
        onChange={onChange}
        {...rest}
      >
        {options.map((item) => {
          return (
            <MenuItem key={id + "-option-" + item.value} value={item.value}>
              {item.label}
            </MenuItem>
          );
        })}
      </Select>
    </FormControl>
  );
}
