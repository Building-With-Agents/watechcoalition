"use client";
import { NoteDTO } from "@/app/lib/admin/careerPrep";
import { useRouter } from "next/navigation";
import DeleteForeverOutlinedIcon from "@mui/icons-material/DeleteForeverOutlined";
import EditOutlinedIcon from "@mui/icons-material/EditOutlined";
import ArrowDropDownOutlinedIcon from "@mui/icons-material/ArrowDropDownOutlined";
import ArrowDropUpOutlinedIcon from "@mui/icons-material/ArrowDropUpOutlined";
import { useState } from "react";
import { Button } from "@mui/material";
export default function NoteCard(
  props: NoteDTO & { UpdateSelectedId: (a: string, b: string) => void },
) {
  const router = useRouter();
  const [preview, setPreview] = useState<boolean>(false);
  const deleteNote = () => {
    fetch("/api/admin/career-prep/delete-student-notes/" + props.id, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });
    router.refresh();
  };
  const toggleEditMode = () => {
    props.UpdateSelectedId(props.id, props.noteContent);
  };
  return (
    <div>
      <span className="flex items-center justify-between">
        <h3
          className="text-sm text-gray-600 cursor-pointer hover:text-black"
          onClick={() => setPreview(!preview)}
        >
          Posted: {props.updatedAt}{" "}
          {preview ? (
            <ArrowDropUpOutlinedIcon />
          ) : (
            <ArrowDropDownOutlinedIcon />
          )}
        </h3>
        <span className="flex gap-3 px-3">
          <Button
            startIcon={<DeleteForeverOutlinedIcon />}
            color="error"
            onClick={deleteNote}
          >
            Delete
          </Button>
          <Button startIcon={<EditOutlinedIcon />} onClick={toggleEditMode}>
            Edit
          </Button>
        </span>
      </span>
      <hr />
      {preview ? (
        <div
          className="ql-editor border w-600"
          dangerouslySetInnerHTML={{ __html: props.noteContent }}
        ></div>
      ) : (
        ""
      )}
    </div>
  );
}
