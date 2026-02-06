"use client";
import * as React from "react";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Modal from "@mui/material/Modal";
import { FormEvent, useState } from "react";
import { CreateMeetingDTO } from "@/app/lib/admin/careerPrep";

const style = {
  position: "absolute",
  top: "50%",
  left: "50%",
  transform: "translate(-50%, -50%)",
  width: 400,
  bgcolor: "background.paper",
  border: "2px solid #000",
  boxShadow: 24,
  p: 4,
};

export default function AddMeetingModal(params: { jsId: string }) {
  const [open, setOpen] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false); // Tracks if the form was successfully submitted
  const [failed, setFailed] = useState(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    setOpen(false);
    setIsSubmitted(false);
    setFailed(false);
  };
  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = event.currentTarget;
    const formData = new FormData(form);
    const submitButton = event.currentTarget.querySelector(
      'button[type="submit"]',
    ) as HTMLButtonElement;
    if (submitButton) submitButton.disabled = true;
    const meetingData: CreateMeetingDTO = {
      jobseekerId: params.jsId,
      meetingTitle: formData.get("meeting_title") as string,
      meetingDatetime: new Date(formData.get("meeting_datetime") as string),
    };
    try {
      const response = await fetch("/api/jobseekers/career-prep/meeting", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(meetingData), // Send as JSON
      });

      if (!response.ok) {
        // If response is not OK, handle error
        console.log("Failed to create Meeting");
        setFailed(true);
        submitButton.disabled = false;
        return;
      } else {
        // Await the response JSON
        setIsSubmitted(true);
        setFailed(false);
        form.reset();
        const data = await response.json();
        console.log("Meeting created:", data);
      }
    } catch (error) {
      console.error("Error creating meeting:", error);
    }
  };

  return (
    <div>
      <Button onClick={handleOpen}>Add Meeting</Button>
      <Modal
        open={open}
        onClose={handleClose}
        aria-labelledby="modal-modal-title"
        aria-describedby="modal-modal-description"
      >
        <Box sx={style}>
          {failed ? <h2 className="text-red-600">Failed Submission</h2> : ""}
          {isSubmitted ? (
            <div>
              <h2>Success!</h2>
              <p>The meeting was successfully created.</p>
              <Button onClick={handleClose} className="btn">
                Close
              </Button>
            </div>
          ) : (
            <div>
              <form onSubmit={onSubmit} className="space-y-3">
                {/* Meeting Title */}
                <div className="grid grid-cols-1">
                  <label htmlFor="meeting_title">Meeting Title</label>
                  <input type="text" name="meeting_title" required />
                </div>

                {/* Meeting DateTime */}
                <div className="grid grid-cols-1">
                  <label htmlFor="meeting_datetime">Meeting Date & Time</label>
                  <input
                    className="border"
                    type="datetime-local"
                    name="meeting_datetime"
                    required
                  />
                </div>
                <div className="flex justify-end space-x-3">
                  <Button type="button" onClick={handleClose} className="btn">
                    Close
                  </Button>
                  <Button type="submit" className="btn btn-primary">
                    Add Meeting
                  </Button>
                </div>
              </form>
            </div>
          )}
        </Box>
      </Modal>
    </div>
  );
}
