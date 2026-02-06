import React, { SyntheticEvent, useMemo, useState } from "react";
import Autocomplete, {
  AutocompleteChangeDetails,
  AutocompleteChangeReason,
  createFilterOptions,
} from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { debounce } from "@mui/material/utils";

interface CachedFetches<ValueType> {
  [searchTerms: string]: ValueType[];
}

interface Props<ValueType> {
  apiSearchRoute: string;
  fieldLabel: string;
  id?: string | undefined;
  className?: string;
  maxTags?: number;
  noResultsText?: string | undefined;
  allowNewOption?: boolean;
  value: string | ValueType;
  disabled?: boolean;
  onChange: (
    event: SyntheticEvent<Element, Event>,
    value: string | ValueType | null,
    reason: AutocompleteChangeReason,
    details?: AutocompleteChangeDetails<string | ValueType> | undefined,
  ) => void;
  searchingText?: string | undefined;
  searchPlaceholder: string;
  getOptionLabel: (option: ValueType) => string;
}

export default function TextFieldWithAutocomplete<ValueType>({
  apiSearchRoute,
  fieldLabel,
  id,
  className = "",
  noResultsText,
  allowNewOption = true,
  value = "",
  disabled,
  onChange,
  searchingText,
  searchPlaceholder,
  getOptionLabel,
}: Props<ValueType>) {
  const [options, setOptions] = useState<(ValueType | string)[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  const filter = createFilterOptions<ValueType | string>();

  const handleInputChange = useMemo(() => {
    const cachedFetches: CachedFetches<ValueType> = {
      "": [], // Shows nothing when there is no search terms in the input box
    };

    return debounce(
      async (event: SyntheticEvent<Element, Event>, newInputValue: string) => {
        try {
          if (cachedFetches.hasOwnProperty(newInputValue)) {
            setOptions(cachedFetches[newInputValue]); // Update the options with cached fetch data instead of hitting API again
          } else if (newInputValue.length !== 0) {
            const response = await fetch(
              `${apiSearchRoute}${encodeURIComponent(newInputValue)}`,
            );
            const data: ValueType[] = await response.json();
            console.log(data);
            cachedFetches[newInputValue] = data; // Cache the fetch data

            setOptions(data); // Update the options with fetched data
          }
        } catch (error) {
          console.error("Error fetching data:", error);
        }
        setLoading(false);
      },
      500,
    );
  }, [apiSearchRoute, setLoading, setOptions]);

  return (
    <Autocomplete
      className={"flex flex-1 " + className}
      autoComplete
      clearOnBlur
      filterSelectedOptions
      id={id}
      loading={loading}
      loadingText={searchingText}
      noOptionsText={noResultsText}
      disabled={disabled}
      value={value}
      filterOptions={(options, params) => {
        if (loading) {
          return [];
        }

        const filtered = filter(options, params);

        if (allowNewOption) {
          // Suggest the creation of a new option
          if (
            typeof params.inputValue === "string" &&
            params.inputValue !== ""
          ) {
            const optionExists =
              options.findIndex(
                (option) =>
                  typeof option !== "string" &&
                  getOptionLabel(option).trim().toLowerCase() ===
                    params.inputValue.trim().toLowerCase(),
              ) !== -1;
            if (!optionExists) {
              filtered.push(`Add "${params.inputValue}"`);
            }
          }
        }

        return filtered;
      }}
      onChange={(ev, val, reason, details) => {
        if (reason === "selectOption") {
          if (!allowNewOption || typeof val !== "string") {
            onChange(ev, val, reason, details);
          } else {
            onChange(
              ev,
              val.substring('Add "'.length, val.length - 1),
              "createOption",
              details,
            );
          }
        } else if (reason === "clear") {
          onChange(ev, null, reason, details);
        }
      }}
      onInputChange={(event, newValue) => {
        if (newValue !== "") {
          setLoading(true);
        }
        handleInputChange(event, newValue);
      }}
      renderInput={(params) => (
        <TextField
          {...params}
          label={fieldLabel}
          placeholder={searchPlaceholder}
          value={
            typeof value === "string"
              ? value
              : ((value && getOptionLabel(value)) ?? "")
          }
        />
      )}
      options={loading ? [] : options}
      getOptionLabel={(option: string | ValueType) => {
        if (typeof option === "string") {
          return option;
        } else if (getOptionLabel) {
          return getOptionLabel(option);
        }
        return "";
      }}
    />
  );
}
