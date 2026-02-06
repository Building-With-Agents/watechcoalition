import React, { SyntheticEvent, useEffect, useMemo, useState } from "react";
import Autocomplete, {
  AutocompleteChangeDetails,
  AutocompleteChangeReason,
} from "@mui/material/Autocomplete";
import TextField from "@mui/material/TextField";
import { debounce } from "@mui/material/utils";
import { Chip } from "@mui/material";

interface CachedFetches<ValueType> {
  [searchTerms: string]: ValueType[];
}

interface Props<ValueType> {
  apiSearchRoute: string;
  fieldLabel: string;
  id?: string | undefined;
  maxTags?: number;
  noResultsText?: string | undefined;
  onChange?:
    | ((
        event: SyntheticEvent<Element, Event>,
        value: (string | ValueType)[],
        reason: AutocompleteChangeReason,
        details?: AutocompleteChangeDetails<string | ValueType> | undefined,
      ) => void)
    | undefined;
  searchingText?: string | undefined;
  searchPlaceholder: string;
  getTagLabel: ((option: ValueType) => string) | undefined;
  getTagLink?: ((option: ValueType) => string) | undefined;
  initialTags?: string[];
  value?: ValueType[];
}

export default function TagsWithAutocomplete<ValueType>({
  apiSearchRoute,
  fieldLabel,
  id,
  maxTags = -1,
  noResultsText,
  onChange,
  searchingText,
  searchPlaceholder,
  getTagLabel,
  getTagLink,
  initialTags,
  value,
}: Props<ValueType>) {
  const [options, setOptions] = useState<ValueType[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

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
            setLoading(true);
            const response = await fetch(
              `${apiSearchRoute}${encodeURIComponent(newInputValue)}`,
            );
            const data: ValueType[] = await response.json();
            cachedFetches[newInputValue] = data; // Cache the fetch data

            setOptions(data); // Update the options with fetched data
            setLoading(false);
          }
        } catch (error) {
          console.error("Error fetching data:", error);
        }
      },
      500,
    );
  }, [apiSearchRoute, setLoading, setOptions]);

  async function initTags() {
    const initTagsToSelect: ValueType[] = [];
    if (initialTags != null) {
      for (let i = 0; i < initialTags.length; i++) {
        const response = await fetch(`${apiSearchRoute}${initialTags[i]}`);
        const data: ValueType[] = await response.json();
        if (data.length > 0) initTagsToSelect.push(data[0]);
      }
    }
  }

  // Load the init tags once on init
  useEffect(() => {
    initTags();
  }, []);

  return (
    <Autocomplete
      autoComplete
      autoSelect
      filterSelectedOptions
      freeSolo
      id={id}
      loading={loading}
      loadingText={searchingText}
      multiple
      noOptionsText={noResultsText}
      onChange={(ev, val, reason, details) => {
        if (maxTags !== -1 && val.length > maxTags) {
          ev.preventDefault();
          return;
        }
        if (onChange) {
          onChange(ev, val, reason, details);
        }
      }}
      onInputChange={handleInputChange}
      options={loading ? [] : options}
      renderInput={(params) => (
        <TextField
          {...params}
          label={fieldLabel}
          placeholder={searchPlaceholder}
        />
      )}
      renderValue={(valueArray, getItemProps) =>
        valueArray.map((option: string | ValueType, index: number) => {
          const { key, ...props } = getItemProps({ index });
          const link = getTagLink && getTagLink(option as ValueType);
          const label =
            typeof option === "string"
              ? option
              : getTagLabel
                ? getTagLabel(option as ValueType)
                : "";
          if (link && link.length > 0) {
            return (
              <Chip
                color="primary"
                clickable
                onClick={() =>
                  window.open(link, "_blank", "noopener,noreferrer")
                }
                label={label}
                deleteIcon={
                  <svg
                    className="inline-block w-5 fill-white hover:fill-gray-300"
                    focusable="false"
                    aria-hidden="true"
                    viewBox="0 0 24 24"
                    data-testid="CancelIcon"
                  >
                    <path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"></path>
                  </svg>
                }
                key={key}
                {...props}
              />
            );
          }
          return (
            <Chip
              color="primary"
              label={label}
              onClick={() => {}}
              clickable={false}
              deleteIcon={
                <svg
                  className="inline-block w-5 fill-white hover:fill-gray-300"
                  focusable="false"
                  aria-hidden="true"
                  viewBox="0 0 24 24"
                  data-testid="CancelIcon"
                >
                  <path d="M12 2C6.47 2 2 6.47 2 12s4.47 10 10 10 10-4.47 10-10S17.53 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"></path>
                </svg>
              }
              key={key}
              {...props}
            />
          );
        })
      }
      getOptionLabel={(option: string | ValueType) => {
        if (typeof option === "string") {
          return option;
        } else if (getTagLabel) {
          return getTagLabel(option as ValueType);
        }
        return "";
      }}
      value={value}
      sx={{
        "& .MuiChip-filled": {
          height: "auto",
        },
      }}
    />
  );
}
