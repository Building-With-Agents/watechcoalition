"use client";
import { userDataTable } from "@/app/lib/user";
import * as React from "react";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import Paper from "@mui/material/Paper";
import { Role } from "@/data/dtos/UserInfoDTO";
import { Button } from "@mui/material";
import { Autocomplete, TextField } from "@mui/material";
export default function EditUsersTable(params: { users: userDataTable[] }) {
  const [rows, setRows] = React.useState(
    params.users.map((user) => ({
      ...user,
      role: Array.isArray(user.role) ? user.role : user.role.split(","),
    })),
  );

  const handleDelete = async (userId: string, name: string) => {
    if (
      !confirm(
        `Are you sure you want to delete user ${name} with ID ${userId}?`,
      )
    ) {
      return;
    }

    try {
      //example, will fail everytime backend funciton not implmented
      const response = await fetch(`/api/admin/user-management/delete`, {
        method: "DELETE",
        body: JSON.stringify({ userId }),
      });

      if (!response.ok) {
        throw new Error("Failed to delete user. ");
      }

      setRows((prevRows) => prevRows.filter((row) => row.id !== userId));
      alert(`User with ID ${userId} deleted successfully.`);
    } catch (error) {
      console.error(error);
      alert(
        "An error occurred while deleting the user. (Backend not connected for this yet -Damien)",
      );
    }
  };

  const MultiSelect: GridColDef = {
    field: "role",
    headerName: "Roles",
    editable: true,
    width: 500,
    //renderCell:(params)=>(params.formattedValue),
    renderEditCell: (params) => {
      const currentRoles = params.value || []; // Handle cases where roles are undefined/null
      return (
        <Autocomplete
          fullWidth
          multiple
          options={Object.values(Role)}
          value={currentRoles}
          renderInput={(params) => (
            <TextField sx={{ margin: 0 }} {...params} placeholder="Add roles" />
          )}
          onChange={(event, newValue) => {
            console.log(newValue);
            params.api.setEditCellValue({
              id: params.id,
              field: params.field,
              value: newValue, // Updates the roles array
            });
            try {
              fetch("/api/admin/user-management/roles/", {
                method: "POST",
                body: JSON.stringify({ userId: params.id, newRoles: newValue }),
              }).then((res) => {
                console.log(res);
                if (!res.ok) {
                  params.api.setEditCellValue({
                    id: params.id,
                    field: params.field,
                    value: params.value, // return to old value on failure to update
                  });
                }
              });
            } catch (error) {
              console.error("Falied to upate roles: ", error);
            }
          }}
        />
      );
    },
  };
  const columns: GridColDef[] = [
    { field: "id", headerName: "ID", width: 70 },
    {
      field: "first_name",
      headerName: "First name",
      width: 130,
      editable: true,
    },
    { field: "last_name", headerName: "Last name", width: 130 },
    { field: "email", headerName: "email", width: 200 },
    MultiSelect,
    { field: "zip", headerName: "zip" },
    { field: "is_marked_deletion", headerName: "Marked For Deletion" },
    {
      field: "actions",
      headerName: "Actions",
      width: 150,
      renderCell: (params) => (
        <Button
          variant="outlined"
          color="error"
          onClick={() =>
            handleDelete(
              params.row.id,
              params.row.first_name + " " + params.row.last_name,
            )
          }
        >
          Delete
        </Button>
      ),
    },
  ];

  return (
    <Paper sx={{ height: 1000, width: "100%" }}>
      <DataGrid
        rows={rows}
        columns={columns}
        pageSizeOptions={[5, 10, 100]}
        sx={{ border: 0 }}
        getRowId={(row) => row.id}
      />
    </Paper>
  );
}
