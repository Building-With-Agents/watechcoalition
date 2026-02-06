import parsePhoneNumberFromString from "libphonenumber-js";

//unused probably left over from next tutorial
// export const generatePagination = (currentPage: number, totalPages: number) => {
//   // If the total number of pages is 7 or less,
//   // display all pages without any ellipsis.
//   if (totalPages <= 7) {
//     return Array.from({ length: totalPages }, (_, i) => i + 1);
//   }

//   // If the current page is among the first 3 pages,
//   // show the first 3, an ellipsis, and the last 2 pages.
//   if (currentPage <= 3) {
//     return [1, 2, 3, '...', totalPages - 1, totalPages];
//   }

//   // If the current page is among the last 3 pages,
//   // show the first 2, an ellipsis, and the last 3 pages.
//   if (currentPage >= totalPages - 2) {
//     return [1, 2, '...', totalPages - 2, totalPages - 1, totalPages];
//   }

//   // If the current page is somewhere in the middle,
//   // show the first page, an ellipsis, the current page and its neighbors,
//   // another ellipsis, and the last page.
//   return [
//     1,
//     '...',
//     currentPage - 1,
//     currentPage,
//     currentPage + 1,
//     '...',
//     totalPages,
//   ];
// };

/**
 * Maps a string value to its corresponding value in an enum type.
 *
 * @param {string | null} value - The value to map to the enum.
 * @param {object} enumType - The enum type to map to.
 * @returns {any} - The mapped value in the enum type.
 * @throws {Error} - If the value does not exist in the enum.
 */
export const mapToEnumOrThrow = (value: string | null, enumType: any): any => {
  if (value == null) {
    return null;
  }
  if (value == undefined) {
    return undefined;
  }

  const enumValues = Object.values(enumType);

  if (!enumValues.includes(value)) {
    throw new Error(`Value "${value}" does not exist in the enum.`);
  }

  return value;
};

/**
 * Maps a string value to an enum member.
 *
 * @param {string | null} value - The string value to be mapped to an enum member.
 * @param {any} enumType - The enum type to map the value to.
 * @returns {any | null} - The enum member corresponding to the value, or null if the value is not present in the enum.
 */
export const mapToEnum = (value: string | null, enumType: any): any => {
  if (value == null || value == undefined) {
    return null;
  }

  const enumValues = Object.values(enumType);

  if (!enumValues.includes(value)) {
    return null; // Return null instead of throwing an error
  }

  return value;
};

/**
 * Normalizes a date string to the ISO 8601 format.
 *
 * @param {string} date - The date string to be normalized.
 * @returns {string} - The normalized date string in the ISO 8601 format.
 */
export const normalizeDate = (date: string): string => {
  const d = new Date(date);
  d.setUTCDate(1);
  d.setUTCHours(0, 0, 0, 0);
  return d.toISOString();
};

export const calculateDaysAway = (date: Date): number => {
  const now = new Date();

  // Normalize the dates to account for local midnight
  const d1 = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const d2 = new Date(date.getFullYear(), date.getMonth(), date.getDate());

  // Calculate the difference in milliseconds
  const diffInMs = d2.getTime() - d1.getTime();

  // Convert milliseconds to days
  const diffInDays = Math.floor(diffInMs / (1000 * 60 * 60 * 24));

  return diffInDays;
};

/**
 * Formats a phone number in E.164 format.
 * @param {string|null} phoneCountryCode - The country code of the phone number.
 * @param {string|null} phone - The phone number to format.
 * @returns {string|null} - The formatted phone number in E.164 format, or null if the phone number is invalid.
 */
export const formatPhoneE164 = (
  phoneCountryCode?: string | null,
  phone?: string | null,
) => {
  const countryCodeMatch = phoneCountryCode?.match(/\+\d+(-\d+)?/);
  const extractedCountryCode = countryCodeMatch ? countryCodeMatch[0] : null;
  if (phone && extractedCountryCode) {
    try {
      const phoneNumber = parsePhoneNumberFromString(
        `${extractedCountryCode}${phone}`,
      );
      if (phoneNumber && phoneNumber.isValid()) {
        return phoneNumber.format("E.164");
      }
      return null;
    } catch (e: any) {
      console.error("Error formatting phone number:", e.message);
    }
  }
};

/**
 * Logs messages or objects to the console during development environment.
 *
 * @param {string | Record<string, any> | null | undefined} labelOrObject - The label or object to log.
 * @param {any} [objOrMessage] - The object or message to log.
 *
 * @returns {void}
 */
export const devLog = (
  labelOrObject: string | Record<string, any> | null | undefined,
  objOrMessage?: any,
): void => {
  if (process.env.NODE_ENV === "development") {
    if (typeof labelOrObject === "string") {
      // Case 2: `devLog('label', object)` or `devLog('label', string)`
      if (objOrMessage === null) {
        // Log label with 'null'
        console.log(labelOrObject, "null");
      } else if (objOrMessage === undefined) {
        // Log label with 'undefined'
        console.log(labelOrObject, "undefined");
      } else if (typeof objOrMessage === "object") {
        // Logging an object with a label
        console.log(
          labelOrObject,
          JSON.stringify(objOrMessage, getCircularReplacer(), 2),
        );
      } else {
        // Logging a string with a label
        console.log(labelOrObject, objOrMessage);
      }
    } else if (labelOrObject === null) {
      // Case 4: Log 'null' directly
      console.log("null");
    } else if (labelOrObject === undefined) {
      // Case 5: Log 'undefined' directly
      console.log("undefined");
    } else if (typeof labelOrObject === "object") {
      // Case 1: `devLog(object)`
      console.log(JSON.stringify(labelOrObject, getCircularReplacer(), 2));
    } else {
      // Case 3: `devLog(string)` - Logging a simple string
      console.log(labelOrObject);
    }
  }
};

// Helper function to handle circular references
const getCircularReplacer = () => {
  const seen = new WeakSet();
  return (key: string, value: any) => {
    if (typeof value === "object" && value !== null) {
      if (seen.has(value)) {
        return "[Circular]";
      }
      seen.add(value);
    }
    return value;
  };
};
