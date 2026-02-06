import {
  FormControl,
  InputLabel,
  MenuItem,
  OutlinedInput,
  Select,
  SelectChangeEvent,
} from "@mui/material";
import CircularProgress from "@mui/material/CircularProgress";
import React from "react";

interface Props<ValueType> {
  id: string;
  className?: string;
  apiAutoloadRoute: string;
  disabled?: boolean;
  label: string;
  value: ValueType | null;
  onChange: (val: ValueType | null) => void;
  placeholder?: string;
  loadingText?: string;
  getOptionLabel: (option: ValueType) => string;
  getOptionId: (option: ValueType) => string;
  getOptionFromId: (options: ValueType[], label: string) => ValueType | null;
  [key: string]: any;
}

export default function SelectAutoload<ValueType>({
  id,
  className = "",
  apiAutoloadRoute,
  disabled = false,
  label,
  value,
  onChange,
  placeholder,
  loadingText = "Loading dropdown...",
  getOptionLabel,
  getOptionId,
  getOptionFromId,
  ...rest
}: Props<ValueType>) {
  const [options, setOptions] = React.useState<ValueType[]>([]);
  const [loading, setLoading] = React.useState(true);

  const selectValue = value ? getOptionId(value) : "";

  const handleChange = (event: SelectChangeEvent<string>) => {
    const selectedValue = event.target.value;
    const selectedOption = getOptionFromId(options, selectedValue);
    onChange(selectedOption);
  };

  // Load the inital filter values
  React.useEffect(() => {
    const autoload = async () => {
      try {
        setLoading(true);

        const response = await fetch(apiAutoloadRoute);
        const data: ValueType[] = await response.json();
        setOptions(data);

        setLoading(false);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setLoading(false);
      }
    };
    autoload();
  }, [apiAutoloadRoute]);

  const renderLoadingSelect = () => (
    <Select
      displayEmpty
      value=""
      disabled
      renderValue={() => (
        <span className="text-gray-500">
          <CircularProgress color="inherit" size={20} /> {loadingText}
        </span>
      )}
    >
      <MenuItem disabled>
        <span>
          <CircularProgress color="inherit" size={20} /> {loadingText}
        </span>
      </MenuItem>
    </Select>
  );

  const renderLoadedSelect = () => (
    <Select
      id={id}
      displayEmpty
      value={selectValue}
      onChange={handleChange}
      input={<OutlinedInput notched label={label} />}
      renderValue={(selected) => {
        if (!selected) {
          return <span className="text-gray-500">{placeholder}</span>;
        }
        const option = getOptionFromId(options, selected);
        return option ? (
          getOptionLabel(option)
        ) : (
          <span className="text-gray-500">{placeholder}</span>
        );
      }}
      inputProps={{ "aria-label": label }}
      {...rest}
    >
      <MenuItem disabled value="">
        {placeholder}
      </MenuItem>
      {options.map((option) => (
        <MenuItem key={getOptionId(option)} value={getOptionId(option)}>
          {getOptionLabel(option)}
        </MenuItem>
      ))}
    </Select>
  );

  return (
    <div className={className}>
      <FormControl disabled={disabled} fullWidth variant="outlined">
        <InputLabel htmlFor={id} shrink>
          {label}
        </InputLabel>
        {loading ? renderLoadingSelect() : renderLoadedSelect()}
      </FormControl>
    </div>
  );
}
