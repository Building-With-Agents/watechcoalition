"use client";

import { useMemo } from "react";
import DOMPurify from "dompurify";

interface SanitizedHtmlProps {
  html: string;
  className?: string;
}

/**
 * Renders HTML sanitized with DOMPurify to prevent XSS.
 * Use for user-generated or external content (e.g. Quill editor output).
 */
export default function SanitizedHtml({ html, className }: SanitizedHtmlProps) {
  const sanitized = useMemo(() => DOMPurify.sanitize(html || ""), [html]);
  return (
    <div
      dangerouslySetInnerHTML={{ __html: sanitized }}
      className={className}
    />
  );
}
