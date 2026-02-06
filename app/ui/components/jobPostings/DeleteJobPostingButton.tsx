"use client";

import { DeleteOutlined } from "@mui/icons-material";
import { useRouter } from "next/navigation";
import PillButton from "../PillButton";

export default function DeleteJobPostingButton(params: { id: string }) {
  const router = useRouter();
  const save = async () => {
    try {
      const response = await fetch(`/api/joblistings/delete/${params.id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(`Error: ${response.status}`);
      }
      router.refresh();
      const data = await response.json();
      console.log("Job post DELETED successfully:", data);
      return data;
    } catch (error) {
      console.error("Error saving job post:", error);
    }
  };
  return (
    <PillButton
      variant="outlined"
      color="error"
      startIcon={<DeleteOutlined />}
      onClick={save}
    >
      Delete
    </PillButton>
  );
}
