"use client";
import { CareerPrepStatus } from "@/app/lib/admin/careerPrep";
import { Alert, Snackbar } from "@mui/material";
import { useRouter } from "next/navigation";
import { useState } from "react";

export default function EnrollmentStatusDropDown(props: {
  careerPrepEnrollmentStatus: CareerPrepStatus;
  jobseekerId: string;
}) {
  const router = useRouter();
  const [openSnackbar, setOpenSnackbar] = useState(false);
  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    //todo add fetch call here to update status
    const newStatus = event.target.value as CareerPrepStatus;
    console.log("change detected: ", props.jobseekerId);
    fetch("/api/admin/career-prep/update-card/", {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        jobseekerId: props.jobseekerId,
        status: newStatus,
      }),
    })
      .then((response) => {
        if (!response.ok) {
          event.target.value = props.careerPrepEnrollmentStatus;
          alert("Enrollment Status update failed");
        } else {
          setOpenSnackbar(true);
        }
        return response.json();
      })
      .then((data) => {
        console.log("Status updated successfully:", data);
        router.refresh();
      })
      .catch((error) => {
        console.error("Error updating status:", error);
      });
  };
  const handleSnackbarClose = (
    event?: React.SyntheticEvent | Event,
    reason?: string,
  ) => {
    if (reason === "clickaway") return;
    setOpenSnackbar(false);
  };
  return (
    <>
      <select
        onChange={handleChange}
        defaultValue={props.careerPrepEnrollmentStatus}
      >
        {props.careerPrepEnrollmentStatus == undefined ? (
          <option>Unknown</option>
        ) : (
          ""
        )}
        {Object.values(CareerPrepStatus).map((stat) => (
          <option
            key={stat}
            value={stat}
            //   selected={stat == props.careerPrepEnrollmentStatus}
          >
            {stat}
          </option>
        ))}
      </select>
      <Snackbar
        open={openSnackbar}
        autoHideDuration={1000}
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert>Enrollment updated successfully!</Alert>
      </Snackbar>
    </>
  );
}
