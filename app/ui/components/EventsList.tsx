"use client";

import { Card, Divider, Grid, Stack, Typography } from "@mui/material";
import PillButton from "./PillButton";
import { EventTypeEnum, PastEventGraceDuration } from "@/app/lib/events";
import Event, { EventData } from "@/app/ui/components/Event";
import React, { useEffect } from "react";

interface EventsListProps {
  headerText: string;
  showOnlyRegisteredEvents: boolean;
  showMeetingLinks: boolean;
}

export default function EventsList({
  headerText,
  showOnlyRegisteredEvents,
  showMeetingLinks,
}: EventsListProps) {
  const [loading, setLoading] = React.useState(true);
  const [showPast, setShowPast] = React.useState(false);
  const [upcomingEvents, setUpcomingEvents] = React.useState<EventData[]>([]);
  const [pastEvents, setPastEvents] = React.useState<EventData[]>([]);
  const [displayEvents, setDisplayEvents] = React.useState<EventData[]>([]);
  const [registeredEvents, setRegisteredEvents] = React.useState<any[]>([]);

  const sortEvents = (events: EventData[]) => {
    // separate events into past and upcoming
    const now = Date.now();
    const past = events.filter((event) => new Date(event.date).getTime() < now);
    past.reverse(); // show most recent past events first
    const upcoming = events.filter(
      (event) => new Date(event.date).getTime() + PastEventGraceDuration > now,
    );

    setPastEvents(past);
    setUpcomingEvents(upcoming);
    setDisplayEvents(showPast ? past : upcoming);
    setLoading(false);
  };

  const getAllEvents = () => {
    fetch("/api/events")
      .then((res) => {
        if (!res.ok) {
          throw new Error("Failed to fetch events");
        }
        return res.json();
      })
      .then((data) => {
        if (showOnlyRegisteredEvents) {
          // request registered events
          fetch("/api/events/registered")
            .then((res) => {
              if (!res.ok) {
                throw new Error("Failed to fetch registered events");
              }
              return res.json();
            })
            .then((registered) => {
              setRegisteredEvents(registered.events);
              const filteredEvents = data.events.filter(
                (event: { id: string }) =>
                  registered.events.some(
                    (e: { eventId: string }) => e.eventId === event.id,
                  ),
              );
              sortEvents(filteredEvents);
            })
            .catch((error) => {
              console.error("Error fetching registered events:", error);
              // Optionally, update UI to show an error message to users
            });
        } else {
          // otherwise, show all events
          sortEvents(data.events);
        }
      })
      .catch((error) => {
        console.error("Error fetching events:", error);
        // Optionally, update UI to show an error message to users
      });
  };

  useEffect(getAllEvents, []);

  const registered = function (id: string) {
    return registeredEvents?.some((e) => e.eventId === id);
  };

  return (
    <Grid container rowSpacing={2} columns={1}>
      <Grid
        spacing={1}
        container
        size={1}
        sx={{ justifyContent: "space-between" }}
      >
        <p className="self-center text-xl font-medium text-button-secondary-idle-text">
          {headerText}
        </p>
        <Stack
          direction={"row"}
          gap={2}
          sx={{
            justifyContent: "center",
            alignItems: "center",
            alignSelf: "stretch",
          }}
        >
          <PillButton
            color={showPast ? "inherit" : "secondary"}
            onClick={() => {
              setShowPast(false);
              setDisplayEvents(upcomingEvents);
            }}
          >
            Upcoming
          </PillButton>
          <Typography
            variant="h4"
            sx={{ fontSize: "24px", textAlign: "center", fontWeight: 400 }}
          >
            |
          </Typography>
          <PillButton
            color={showPast ? "secondary" : "inherit"}
            onClick={() => {
              setShowPast(true);
              setDisplayEvents(pastEvents);
            }}
          >
            Past
          </PillButton>
        </Stack>
        {showOnlyRegisteredEvents && (
          <PillButton
            color="inherit"
            href="/services/events"
            sx={{
              color: "secondary.main",
            }}
          >
            All Events
          </PillButton>
        )}
        {!showOnlyRegisteredEvents && (
          <PillButton
            color="inherit"
            href="/services/events/registered"
            sx={{
              color: "secondary.main",
            }}
          >
            My Events
          </PillButton>
        )}
      </Grid>
      <Grid container sx={{ width: "100%" }}>
        <Card
          variant="outlined"
          sx={{
            width: "100%",
            pt: 1,
            px: 1,
            alignItems: "center",
          }}
        >
          {loading && <p className="text-center my-4">Loading...</p>}
          {!loading && displayEvents?.length === 0 && (
            <p className="text-center">No events found</p>
          )}
          {!loading &&
            displayEvents?.map((event, i, arr) => (
              <React.Fragment key={i}>
                <Event
                  showLink={showMeetingLinks}
                  registered={registered(event.id)}
                  event={{
                    ...event,
                    eventType: event.eventType as EventTypeEnum,
                  }}
                />
                {i < arr.length - 1 && <Divider sx={{ my: 1 }} />}
              </React.Fragment>
            ))}
        </Card>
      </Grid>
    </Grid>
  );
}
