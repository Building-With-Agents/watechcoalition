"use client";
import React, { useState, ReactNode } from "react";
import { Bookmark, BookmarkBorderOutlined } from "@mui/icons-material";
import PillButton from "./PillButton";

interface BookmarkProps {
  bookmarked: boolean;
  addUrl: string;
  removeUrl: string;
  bookmarkedText?: string;
  unbookmarkedText?: string;
  bookmarkedIcon?: ReactNode;
  unbookmarkedIcon?: ReactNode;
  onBookmarkChange?: (isBookmarked: boolean) => void;
}

function BookmarkWithTextComponent({
  bookmarked,
  addUrl,
  removeUrl,
  bookmarkedText = "Remove Job",
  unbookmarkedText = "Save Job",
  bookmarkedIcon = <Bookmark />,
  unbookmarkedIcon = <BookmarkBorderOutlined />,
  onBookmarkChange,
}: BookmarkProps) {
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

      if (response.ok) {
        onBookmarkChange?.(!bookmarked);
      } else {
        setIsBookmarked(initialState);
      }
    } catch (error) {
      console.error("Error toggling bookmark:", error);
      setIsBookmarked(initialState);
    }
  }

  return isBookmarked ? (
    <PillButton
      startIcon={bookmarkedIcon}
      onClick={toggleBookmark}
      color="inherit"
      sx={{ color: "secondary.main" }}
    >
      {bookmarkedText}
    </PillButton>
  ) : (
    <PillButton
      startIcon={unbookmarkedIcon}
      onClick={toggleBookmark}
      color="inherit"
      sx={{ color: "secondary.main" }}
    >
      {unbookmarkedText}
    </PillButton>
  );
}

export default React.memo(BookmarkWithTextComponent);
