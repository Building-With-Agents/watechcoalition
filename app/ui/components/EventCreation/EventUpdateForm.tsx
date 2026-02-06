"use client";

import { useEffect, useState } from "react";
import { Button } from "@mui/material";
import { EventTypeEnum, EventUpdateData } from "@/app/lib/events";
import { Events } from "@prisma/client";
import { useQuill } from "react-quilljs";
import "quill/dist/quill.snow.css";

export default function EventUpdateForm() {
  const { quill, quillRef } = useQuill();
  // State to manage form input values
  const [selectedEventId, setSelectedEventId] = useState<string>();
  const [existingEvents, setExistingEvents] = useState<Events[]>();

  const [eventName, setEventName] = useState<string>("");
  const [eventDescription, setEventDescription] = useState<string>("");
  const [eventLocation, setEventLocation] = useState<string>("");
  const [eventDate, setEventDate] = useState<string>("");
  const [isRegisterLink, setIsRegisterLink] = useState<boolean>(true);
  const [registerLink, setRegisterLink] = useState<string>("");
  const [duration, setDuration] = useState<number>(90);
  const [joinMeetingLink, setJoinMeetingLink] = useState("");
  const [recordingLink, setRecordingLink] = useState<string>("");
  // const [eventBlurb, setEventBlurb] = useState<string>("");
  const [eventType, setEventType] = useState<EventTypeEnum>(
    EventTypeEnum.General,
  ); // Consider using a union type for stricter control
  // Handle form submission
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    const submitButton = event.currentTarget.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    if (submitButton) submitButton.disabled = true;
    // Form data to send to backend (example)
    const formData: EventUpdateData = {
      name: eventName,
      description: eventDescription,
      location: eventLocation,
      date: new Date(eventDate), // Ensure date is correctly formatted
      registrationLink: registerLink,
      joinMeetingLink: joinMeetingLink,
      recordingLink: recordingLink,
      // blurb: eventBlurb,
      eventType: eventType,
      duration: duration,
    };

    // You can call an API function here to create the event in the database
    try {
      console.log("Event Data Submitted: ", formData);
      const response = await fetch(`/api/events`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          eventId: selectedEventId,
          updatedData: formData,
        }),
      });

      if (!response.ok) {
        console.error("Failed");
        if (submitButton) submitButton.disabled = false;
        return;
      } else {
        const data = await response.json();
        console.log("Update sucsess: ", data);
        if (submitButton) submitButton.disabled = false;
        alert("Event updated successfully!");
        getExistingEvents();
        setSelectedEventId(undefined);
      }
    } catch (error) {
      console.error("Error:", error);
      if (submitButton) submitButton.disabled = false;
    }
  };
  const handleDelete = async () => {
    try {
      const response = await fetch(`/api/events`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ eventId: selectedEventId }),
      });
      if (!response.ok) {
        console.error("Failed");
        alert("Delete Failed");
      } else {
        alert("Delete Success");
        setExistingEvents((prev) =>
          prev?.filter((e) => e.id != selectedEventId),
        );
        resetForm();
      }
    } catch (error) {
      alert("Delete Failed: " + error);
    }
  };
  const resetForm = () => {
    setEventName("");
    setEventDate("");
    setRegisterLink("");
    setJoinMeetingLink("");
    setRecordingLink("");
    // setEventBlurb("");
    setEventLocation("");
    setEventDescription("");
    setEventType(EventTypeEnum.General);
    setSelectedEventId("");
  };
  const getExistingEvents = () => {
    fetch("/api/events")
      .then((res) => {
        if (!res.ok) {
          throw new Error("Failed to fetch events");
        }
        return res.json();
      })
      .then((data) => {
        setExistingEvents(data.events);
      })
      .catch((error) => {
        console.error("Error fetching events:", error);
        // Optionally, update UI to show an error message to users
      });
  };

  useEffect(getExistingEvents, []);
  useEffect(() => {
    const selectedEvent = existingEvents?.find(
      (ev) => ev.id == selectedEventId,
    );
    if (selectedEvent != undefined) {
      const eventDate = new Date(selectedEvent.date);
      // Convert to local time format required for datetime-local input
      const localDateTime = new Date(
        eventDate.getTime() - eventDate.getTimezoneOffset() * 60000,
      )
        .toISOString()
        .slice(0, 16); // Trim to YYYY-MM-DDTHH:mm
      setEventName(selectedEvent.name);
      setEventDate(localDateTime);
      setIsRegisterLink(
        selectedEvent.registrationLink != null &&
          selectedEvent.registrationLink != "",
      );
      setRegisterLink(selectedEvent.registrationLink ?? "");
      setJoinMeetingLink(selectedEvent.joinMeetingLink ?? "");
      setRecordingLink(selectedEvent.recordingLink ?? "");
      setDuration(selectedEvent.duration);

      // setEventBlurb(selectedEvent.blurb ?? "");
      setEventLocation(selectedEvent.location);
      setEventDescription(selectedEvent.description ?? "");
      setEventType(selectedEvent.eventType as EventTypeEnum);

      if (quill) {
        quill.clipboard.dangerouslyPasteHTML(selectedEvent.description ?? "");
      }
    }
  }, [selectedEventId]);

  useEffect(() => {
    if (quill) {
      quill.clipboard.dangerouslyPasteHTML(eventDescription);
      quill.on("text-change", () => {
        setEventDescription(quill.root.innerHTML);
      });
    }
  }, [quill]);

  return (
    <form
      onSubmit={handleSubmit}
      className="space-y-4 p-4 border rounded-lg shadow-md"
    >
      <h2 className="text-2xl font-semibold">Update an Event</h2>
      <select
        value={selectedEventId || ""}
        onChange={(e) => {
          setSelectedEventId(e.target.value);
        }}
        className="mt-2 p-2 border rounded-xs w-full"
      >
        <option value="">--Please Select An Event--</option>
        {existingEvents?.map((ev) => (
          <option key={ev.id} value={ev.id}>
            {ev.name} - {new Date(ev.date).toLocaleDateString()}
          </option>
        ))}
      </select>
      {selectedEventId && (
        <>
          <div>
            <label htmlFor="eventTitle" className="block text-sm font-medium">
              Event Title
            </label>
            <input
              type="text"
              id="eventTitle"
              value={eventName}
              onChange={(e) => setEventName(e.target.value)}
              required
              className="mt-2 p-2 border rounded-xs w-full"
            />
          </div>
          <div>
            <label
              htmlFor="eventLocation"
              className="block text-sm font-medium"
            >
              Event Location (Remote or Physical Address)
            </label>
            <input
              type="text"
              id="eventLocation"
              value={eventLocation}
              onChange={(e) => setEventLocation(e.target.value)}
              required
              className="mt-2 p-2 border rounded-xs w-full"
            />
          </div>

          <div>
            <label htmlFor="eventDate" className="block text-sm font-medium">
              Event Date
            </label>
            <input
              type="datetime-local"
              id="eventDate"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              required
              className="mt-2 p-2 border rounded-xs w-full"
            />
          </div>
          <div>
            <label htmlFor="duration" className="block text-sm font-medium">
              Event Duration(in minutes)
            </label>
            <input
              id="duration"
              type="number"
              value={duration}
              onChange={(e) => setDuration(e.target.value as unknown as number)}
              required
              className="mt-2 p-2 border rounded-xs w-full"
            />
          </div>

          <div className="flex flex-row gap-2">
            <label htmlFor="linkType" className="block text-sm font-medium">
              What link will attendees use for this event?
            </label>
            <input
              type="radio"
              id="registerLink"
              value={"Register Link"}
              name={"linkType"}
              onChange={() => {
                setIsRegisterLink(true);
                setJoinMeetingLink("");
              }}
              checked={isRegisterLink}
              required
              className="p-2"
            />
            <label htmlFor="registerLink" className="block text-sm font-medium">
              Register Link
            </label>
            <input
              type="radio"
              id="joinLink"
              value={"Public Join Link"}
              name={"linkType"}
              onChange={() => {
                setIsRegisterLink(false);
                setRegisterLink("");
              }}
              checked={!isRegisterLink}
              required
              className="p-2"
            />
            <label htmlFor="joinLink" className="block text-sm font-medium">
              Public Join Link
            </label>
          </div>

          {isRegisterLink && (
            <div>
              <label htmlFor="zoomLink" className="block text-sm font-medium">
                Registration Link (join meeting via email confirmation)
              </label>
              <input
                type="url"
                id="zoomLink"
                value={registerLink}
                onChange={(e) => setRegisterLink(e.target.value)}
                required
                className="mt-2 p-2 border rounded-xs w-full"
              />
            </div>
          )}
          {!isRegisterLink && (
            <div>
              <label htmlFor="joinLink" className="block text-sm font-medium">
                Public Join Link (no Zoom registration required)
              </label>
              <input
                type="url"
                id="joinLink"
                value={joinMeetingLink}
                onChange={(e) => setJoinMeetingLink(e.target.value)}
                required
                className="mt-2 p-2 border rounded-xs w-full"
              />
            </div>
          )}
          <div>
            <label
              htmlFor="recordingLink"
              className="block text-sm font-medium"
            >
              Recording link (optional, will replace join link)
            </label>
            <input
              type="url"
              id="recordingLink"
              value={recordingLink}
              onChange={(e) => setRecordingLink(e.target.value)}
              className="mt-2 p-2 border rounded-xs w-full"
            />
          </div>
          {/* <div>
            <label htmlFor="eventBlurb" className="block text-sm font-medium">
              Event Blurb
            </label>
            <input
              id="eventBlurb"
              value={eventBlurb}
              onChange={(e) => setEventBlurb(e.target.value)}
              required
              className="mt-2 p-2 border rounded-xs w-full"
            />
          </div> */}
          <div>
            <label
              htmlFor="eventDescription"
              className="block text-sm font-medium"
            >
              Event Description
            </label>
            <div ref={quillRef} style={{ minHeight: "200px" }} />
          </div>
          <div>
            <label htmlFor="eventType" className="block text-sm font-medium">
              Event Type
            </label>
            <select
              id="eventType"
              value={eventType}
              onChange={(e) => setEventType(e.target.value as EventTypeEnum)} // Cast to EventType
              className="mt-2 p-2 border rounded-xs w-full"
            >
              {Object.values(EventTypeEnum).map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>

          <div className="mt-4">
            <Button onClick={handleDelete}>Delete Event</Button>
            <Button type="submit">Update Event</Button>
          </div>
        </>
      )}
    </form>
  );
}
