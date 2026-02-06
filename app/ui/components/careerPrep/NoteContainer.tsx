"use client";
import { NoteType, NoteDTO } from "@/app/lib/admin/careerPrep";
import MarkDownEditor from "../mdEditor/MarkDownEditor";
import NoteCard from "./NoteCard";
import { useState } from "react";
import { AddOutlined } from "@mui/icons-material";

export default function NoteContainer(params: {
  noteType: NoteType;
  jsId: string;
  notes: NoteDTO[];
}) {
  const [selectedNoteId, setSelectedNoteId] = useState<string>("");
  const [starterContent, setStarterContent] = useState<string>("");
  const handleNoteSelection = (noteId: string, noteContent: string) => {
    setSelectedNoteId(noteId);
    setStarterContent(noteContent);
  };
  const NewNote = () => {
    setSelectedNoteId("");
    setStarterContent("");
  };
  return (
    <div className="flex justify-between flex-wrap py-4">
      <MarkDownEditor
        key={(params.noteType as string) + selectedNoteId} // Ensure a unique key for each selection
        noteType={params.noteType} // Use dynamic noteType from params
        jobseekerId={params.jsId}
        noteid={selectedNoteId}
        starterContent={starterContent}
      />
      <div className="h-[525px] overflow-auto border">
        <button
          className="border w-[600px] h-[60px] bg-blue-background text-white"
          onClick={NewNote}
        >
          New Note <AddOutlined />
        </button>
        {params.notes
          .sort(
            (a, b) =>
              new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime(),
          )
          .map((n) => (
            <NoteCard
              UpdateSelectedId={handleNoteSelection}
              key={n.id}
              {...n}
            />
          ))}
      </div>
    </div>
  );
}
