"use client";
import "@/app/ui/profile-creation.css";
import ProfileCreationHeader from "@/app/ui/ProfileCreationHeader";

// REVIEW: You can locate the store in the layout component if all the routes using that layout need the store.
import JobseekerStoreProvider from "../../../JobseekerStoreProvider";
import { LocalizationProvider } from "@mui/x-date-pickers";
import { AdapterDayjs } from "@mui/x-date-pickers/AdapterDayjs";

export default function ProfileCreationLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="en">
        <ProfileCreationHeader />
        <JobseekerStoreProvider>{children}</JobseekerStoreProvider>
      </LocalizationProvider>
    </div>
  );
}
