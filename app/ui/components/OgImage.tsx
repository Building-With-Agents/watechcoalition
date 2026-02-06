"use client";
import { CircularProgress, Grid } from "@mui/material";
import { useEffect, useState } from "react";

interface OgImageProps {
  siteUrl: string;
  alt?: string;
}

export default function OgImage({ siteUrl, alt }: OgImageProps) {
  const [ogImage, setOgImage] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchOgImage() {
      if (!siteUrl) {
        setLoading(false);
        return;
      }
      try {
        const res = await fetch(`/api/ogs?url=${encodeURIComponent(siteUrl)}`);
        const data = await res.json();
        setOgImage(data.image);
      } catch (error) {
        console.error("Error fetching OG image:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchOgImage();
  }, [siteUrl]);

  if (loading) {
    return (
      <Grid
        container
        sx={{
          height: "150px",
          backgroundColor: "neutral.100",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <CircularProgress />
      </Grid>
    );
  }
  if (!ogImage) {
    return (
      <Grid
        container
        sx={{
          height: "150px",
          backgroundColor: "neutral.100",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <p>No preview available.</p>
      </Grid>
    );
  }
  return <img src={ogImage} alt={alt} />;
}
