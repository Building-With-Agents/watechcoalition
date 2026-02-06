import { getSession, useSession } from "next-auth/react";
import { devLog } from "@/app/lib/utils";
import { Role } from "@/data/dtos/UserInfoDTO";

export const useUpdateSession = (): ((
  properties: Record<string, any>,
) => Promise<void>) => {
  const { update } = useSession(); // Ensure we get the update function

  const updateSessionProperties = async (
    properties: Record<string, any>,
  ): Promise<void> => {
    if (typeof update !== "function") {
      console.error('The "update" function is not available.');
      return;
    }

    // Validate each property
    for (const [key, value] of Object.entries(properties)) {
      const isValid =
        typeof value === "string" ||
        typeof value === "boolean" ||
        (Array.isArray(value) &&
          value.every((v) => Object.values(Role).includes(v)));

      if (!isValid) {
        console.error(`Invalid property type for "${key}":`, value);
        return; // Exit if any property is invalid
      }
    }

    // Proceed with the update if validation passes
    try {
      devLog("Properties to update:", properties); // Debug log for properties
      await update(properties); // Call the update function with the validated properties
      const updatedSession = await getSession(); // Fetch the latest session state and log it
      devLog("Updated session:", updatedSession);
      devLog(`Session properties updated successfully.`, "");
    } catch (error) {
      console.error(`Failed to update session properties:`, error);
    }
  };

  return updateSessionProperties; // Return the function
};
