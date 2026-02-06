"use client";
import { useQuill } from "react-quilljs";
import "quill/dist/quill.snow.css";
import { useEffect } from "react";

export default function QuillEditor({
  html,
  onChangeAction,
}: {
  html: string;
  onChangeAction: (val: string) => void;
}) {
  const { quill, quillRef } = useQuill({
    modules: {
      toolbar: [
        ["bold", "italic", "underline", "strike"],
        [{ align: [] }],
        [{ list: "ordered" }, { list: "bullet" }],
        [{ indent: "-1" }, { indent: "+1" }],
      ],
    },
  });
  useEffect(() => {
    if (quill) {
      const currentContent = quill.root.innerHTML;
      const isDefaultEmpty = currentContent === "<p><br></p>";
      if (currentContent !== html && !(isDefaultEmpty && html === "")) {
        quill.clipboard.dangerouslyPasteHTML(html || "<p><br></p>");
      }
    }
  }, [quill, html]);
  const handleBlur = () => {
    if (quill) onChangeAction(quill.root.innerHTML);
  };

  return (
    <div
      ref={quillRef}
      onBlur={handleBlur}
      style={{
        minHeight: 200,
      }}
    />
  );
}
