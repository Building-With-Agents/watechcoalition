"use client";
import { useState } from "react";
interface TabProps {
  label: string;
  content: React.ReactNode;
}

export default function Tabs(props: { tabs: TabProps[] }) {
  const [activeIndex, setActiveIndex] = useState(0);

  return (
    <div className="w-full">
      <div className="flex divide-x-2 divide-inherit rounded-lg border border-solid border-blue-border">
        {props.tabs.map((tab, index) => (
          <button
            key={index}
            onClick={() => setActiveIndex(index)}
            className={`py-2 px-2 grow text-sm 
            ${index === activeIndex ? "bg-blue-background font-bold text-white " : "text-blue-text hover:text-blue-tw600 hover:bg-gray-100 "}
              ${index === 0 ? "rounded-tl-md rounded-bl-md" : ""}
              ${index === props.tabs.length - 1 ? "rounded-tr-md rounded-br-md" : ""}`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {props.tabs.map((tab, index) => (
        <div key={index} className={index === activeIndex ? "" : "hidden"}>
          {tab.content}
        </div>
      ))}
    </div>
  );
}
