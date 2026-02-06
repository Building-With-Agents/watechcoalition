"use client";
import Image from "next/image";
import { useEffect, useState } from "react";
export default function EmployerLandingTabs() {
  const [index, setIndex] = useState<number>(0);
  const tabs = [
    { src: "/images/SearchableDB.svg", text: "Searchable Database", index: 0 },
    {
      src: "/images/SkillGapAnalysis.svg",
      text: "Skills Gap Analysis",
      index: 1,
    },
    { src: "/images/DLTicon.svg", text: "Diverse Local Talent", index: 2 },
  ];
  const Subtitle = [
    "Our searchable database quickly connects you with qualified candidates who match your specific needs.",
    "Uncover hidden tech talent, assess their fit, and quickly find the perfect match for your team—all in one place.",
    "Discover a diverse pool of talented candidates from various backgrounds and experiences, ready to contribute unique perspectives to your team",
  ];
  const Content = [
    "/images/CandidateSearchTabContent.png",
    "/images/SkillsGapContent.png",
    "/images/DiverseLocalContent.png",
  ];
  // Automatically switch tabs every 4 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      setIndex((prevIndex) => (prevIndex < 2 ? prevIndex + 1 : 0));
    }, 4000);

    return () => clearTimeout(timer); // Clean up the timer
  }, [index]);
  return (
    <>
      <div className="text-center font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-[#0f1728]">
        {Subtitle[index]}
      </div>
      <div className="items center flex gap-4">
        {tabs.map((tab, i) => (
          <TabButton
            key={i}
            src={tab.src}
            text={tab.text}
            isSelected={index === tab.index}
            onClick={() => setIndex(tab.index)}
          />
        ))}
      </div>
      {Content.map((content, i) => (
        <Image
          key={i}
          className={i === index ? "" : "hidden"}
          src={content}
          width={588}
          height={432}
          alt=""
        />
      ))}
    </>
  );
}
function TabButton(props: {
  src: string;
  text: string;
  isSelected: boolean;
  onClick: () => void;
}) {
  return (
    <div
      className="inline-flex h-[115px] w-[115px] max-w-[28vw] flex-col items-center justify-center gap-2 rounded-2xl bg-[#f3f3f3] p-4 shadow-xs cursor-pointer"
      onClick={props.onClick}
    >
      <TabImage src={props.src} isSelected={props.isSelected} />
      <div className="text-center font-['Roboto'] text-sm ">{props.text}</div>
    </div>
  );
}

function TabImage(props: { src: string; isSelected: boolean }) {
  return (
    <Image
      className={props.isSelected ? "" : "grayscale"}
      src={props.src}
      alt={""}
      width={48}
      height={48}
    />
  );
}
