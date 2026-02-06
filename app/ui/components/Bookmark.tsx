"use client";
import React, { useState } from "react";
import { IconButton } from "@mui/material";
import { Bookmark, BookmarkBorderOutlined } from "@mui/icons-material";

interface BookmarkProps {
  bookmarked: boolean;
  addUrl: string;
  removeUrl: string;
}

function BookmarkComponent({ bookmarked, addUrl, removeUrl }: BookmarkProps) {
  const [isBookmarked, setIsBookmarked] = useState(bookmarked);
  async function toggleBookmark() {
    const initialState = isBookmarked;
    setIsBookmarked(!isBookmarked);

    const url = isBookmarked ? removeUrl : addUrl;

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });

      if (!response.ok) {
        setIsBookmarked(initialState);
      }
    } catch (error) {
      console.error("Error toggling bookmark:", error);
      setIsBookmarked(initialState);
    }
  }

  return (
    <IconButton onClick={toggleBookmark}>
      {isBookmarked ? (
        <Bookmark sx={{ color: "secondary.main" }} />
      ) : (
        <BookmarkBorderOutlined />
      )}
    </IconButton>
  );
}

export default React.memo(BookmarkComponent);
