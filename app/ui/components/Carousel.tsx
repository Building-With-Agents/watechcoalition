"use client";

import * as React from "react";
import Box from "@mui/material/Box";
import { Radio, Stack } from "@mui/material";

export default function CustomCarousel({
  children,
}: {
  children: React.ReactNode;
}) {
  const childrenArray = React.Children.toArray(children);
  const [currentSlide, setCurrentSlide] = React.useState(0);
  const [touchStartX, setTouchStartX] = React.useState<number>(0);
  const [touchEndX, setTouchEndX] = React.useState<number>(0);
  const totalSlides = childrenArray.length;

  const handleTouchStart = (e: React.TouchEvent<HTMLDivElement>) => {
    setTouchStartX(e.touches[0].clientX);
    setTouchEndX(e.touches[0].clientX);
  };

  const handleTouchMove = (e: React.TouchEvent<HTMLDivElement>) => {
    setTouchEndX(e.touches[0].clientX);
  };

  const handleTouchEnd = () => {
    const delta = touchEndX - touchStartX;
    if (delta > 75) {
      handlePrev();
    } else if (delta < -75) {
      handleNext();
    }
  };

  const handleNext = () => {
    setCurrentSlide((prev) => (prev === totalSlides - 1 ? 0 : prev + 1));
  };

  const handlePrev = () => {
    setCurrentSlide((prev) => (prev === 0 ? totalSlides - 1 : prev - 1));
  };

  return (
    <Box
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
      sx={{
        position: "relative",
        overflow: "hidden",
        touchAction: "pan-y",
      }}
    >
      <Stack
        direction={"row"}
        sx={{
          transform: `translateX(-${currentSlide * (100 / totalSlides)}%)`,
          width: `${totalSlides * 100}%`,
          transition: (theme) =>
            `transform ${theme.transitions.duration.standard}ms ${theme.transitions.easing.easeInOut}`,
        }}
      >
        {childrenArray.map((child, index) => (
          <Box
            key={index}
            sx={{
              minWidth: `${100 / totalSlides}%`,
              padding: 2,
              pointerEvents: index !== currentSlide ? "none" : undefined,
              opacity: index === currentSlide ? 1 : 0.7,
              transition: (theme) =>
                `opacity ${theme.transitions.duration.standard}ms`,
            }}
            aria-hidden={index !== currentSlide}
            inert={index !== currentSlide ? true : undefined}
          >
            {child}
          </Box>
        ))}
      </Stack>
      <Stack direction={"row"} sx={{ justifyContent: "center" }}>
        {childrenArray.map((_, idx) => (
          <Radio
            key={idx}
            checked={currentSlide === idx}
            onClick={() => setCurrentSlide(idx)}
            size="small"
          />
        ))}
      </Stack>
    </Box>
  );
}
