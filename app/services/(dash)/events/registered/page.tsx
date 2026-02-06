import React from "react";
import EventsList from "@/app/ui/components/EventsList";
import { Box } from "@mui/material";

export default function Page() {
  return (
    <Box sx={{ mx: { xs: 3, md: 6.25 }, flex: "flex-1" }}>
      <EventsList
        headerText={"My Events"}
        showOnlyRegisteredEvents={true}
        showMeetingLinks={true}
      ></EventsList>
    </Box>
  );
}
