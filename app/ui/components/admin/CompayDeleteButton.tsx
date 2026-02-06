"use client";
import { Button } from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
export default function CompanyDeleteButton({
  companyId,
}: {
  companyId: string;
}) {
  const handleDelete = async () => {
    const isConfirmed = window.confirm(
      "Are you sure you want to delete this company?",
    );
    if (isConfirmed) {
      try {
        const response = await fetch(`/api/companies/delete`, {
          method: "DELETE",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ companyId: companyId }),
        });

        if (response.ok) {
          alert("Company deleted successfully.");
          // Optionally trigger any necessary UI updates here
        } else {
          const error = await response.json();
          alert(`Failed to delete company: ${error.message}`);
        }
      } catch (err) {
        alert("An error occurred while deleting the company.");
        console.error(err);
      }
    }
  };
  return (
    <Button startIcon={<DeleteIcon />} onClick={handleDelete}>
      Delete
    </Button>
  );
}
