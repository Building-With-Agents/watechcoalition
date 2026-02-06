"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuill } from "react-quilljs";
//https://github.com/gtgalone/react-quilljs#readme
// or const { useQuill } = require('react-quilljs');

import "quill/dist/quill.snow.css"; // Add css for snow theme
import {
  CreateNoteDTO,
  NoteType,
  UpdateNoteDTO,
} from "@/app/lib/admin/careerPrep";
// or import 'quill/dist/quill.bubble.css'; // Add css for bubble theme
export default function MarkDownEditor(props: {
  noteType: NoteType;
  jobseekerId: string;
  noteid?: string;
  starterContent?: string;
}) {
  const { quill, quillRef } = useQuill();
  const now = new Date();
  const [updateDate, setUpdateDate] = useState<string>(
    `${now.getFullYear()}-${(now.getMonth() + 1).toString().padStart(2, "0")}-${now.getDate().toString().padStart(2, "0")}`,
  );
  const router = useRouter();
  React.useEffect(() => {
    if (quill) {
      quill.clipboard.dangerouslyPasteHTML(props.starterContent ?? "");
      quill.on("text-change", () => {
        console.log("Text change!");
        console.log(quill.getText()); // Get text only
        console.log(quill.getContents()); // Get delta contents
        console.log(quill.root.innerHTML); // Get innerHTML using quill
        console.log(quillRef.current.firstChild.innerHTML); // Get innerHTML using quillRef
      });
    }
  }, [quill]);
  const ClearNote = () => {
    quill?.setContents([]);
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const content = quill?.root.innerHTML; // Get editor content as HTML
    const req: CreateNoteDTO = {
      jobseekerId: props.jobseekerId,
      noteType: props.noteType,
      noteContent: content ?? "",
      updatedDate: updateDate ? new Date(updateDate) : undefined,
    };
    try {
      const response = await fetch("/api/admin/career-prep/add-student-notes", {
        //still needs backend api
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(req),
      });

      if (response.ok) {
        console.log("Content submitted successfully");
        ClearNote();
        router.refresh();
      } else {
        console.error("Error submitting content");
      }
    } catch (error) {
      console.error("Request failed", error);
    }
  };
  const deleteNote = () => {
    fetch(
      "/api/admin/career-prep/delete-student-notes/" + (props.noteid ?? ""),
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      },
    );
    ClearNote();
    router.refresh();
  };
  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    const content = quill?.root.innerHTML; // Get editor content as HTML
    const req: UpdateNoteDTO = {
      noteId: props.noteid ?? "",
      noteType: props.noteType,
      noteContent: content ?? "",
      updatedDate: new Date(updateDate),
    };
    try {
      // if(props.setEdit == undefined){
      //   return
      // }
      const response = await fetch(
        "/api/admin/career-prep/update-student-notes",
        {
          //still needs backend api
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(req),
        },
      );

      if (response.ok) {
        console.log("Content submitted successfully");
        //props.setEdit(false)
        router.refresh();
      } else {
        console.error("Error submitting content");
      }
    } catch (error) {
      console.error("Request failed", error);
    }
  };
  return (
    <div className="h-[625px]">
      <div className="w-[650px] h-[400px]">
        <div ref={quillRef} />
        <input
          type="date"
          className="w-full"
          value={updateDate}
          onChange={(e) => {
            setUpdateDate(e.target.value);
          }}
          id="update"
          name="update"
        />
        <br />
        {props.noteid ? (
          <>
            <button
              className="border w-[325px] h-[60px] bg-gray-200"
              onClick={deleteNote}
            >
              Delete Note
            </button>
            <button
              className="border w-[325px] h-[60px] bg-blue-background text-white"
              onClick={handleUpdate}
            >
              Update
            </button>
          </>
        ) : (
          <>
            <button
              className="border w-[325px] h-[60px] bg-gray-200"
              onClick={ClearNote}
            >
              Clear Note
            </button>
            <button
              className="border w-[325px] h-[60px] bg-blue-background text-white"
              onClick={handleSubmit}
            >
              Send
            </button>
          </>
        )}
      </div>
    </div>
  );
}
