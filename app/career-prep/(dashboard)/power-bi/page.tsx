"use client";
import React from "react";

export default function Page() {
  return (
    <div style={{ width: "100%", height: "100vh" }}>
      <iframe
        title="Watech Coalition Dashboard"
        style={{ width: "100%", height: "100%", border: "none" }}
        src="https://app.powerbi.com/reportEmbed?reportId=fa77cb06-c991-4883-98d7-ebae8fc00cff&autoAuth=true&ctid=a3c7a257-40f2-43a9-9373-8bb5fc6862f7&actionBarEnabled=true"
        allowFullScreen={true}
      ></iframe>
    </div>
  );
}
