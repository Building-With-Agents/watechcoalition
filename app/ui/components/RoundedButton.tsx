import Link from "next/link";
import React, { MouseEvent } from "react";

interface Props {
  content: string;
  invertColor: boolean;
  link?: string;
  bold?: boolean;
  snug?: boolean;
  className?: string;
  newColors?: boolean;
  disabled?: boolean;
  onClick?: (e: MouseEvent<HTMLAnchorElement>) => Promise<void>;
}

export default function RoundedButton({
  content,
  link,
  invertColor,
  onClick,
  bold = true,
  snug = false,
  className = "",
  newColors = false,
  disabled = false,
  ...rest
}: Props) {
  const isPrimary = invertColor;
  let bgColorIdle = "";
  let bgColorHover = "";
  let bgColorFocus = "";
  let bgColorActive = "";
  let bgColorVisited = "";
  let bgColorDisabled = "";
  let textColorIdle = "";
  let textColorHover = "";
  let textColorFocus = "";
  let textColorActive = "";
  let textColorVisited = "";
  let textColorDisabled = "";
  let border = "";

  if (newColors) {
    if (isPrimary) {
      bgColorIdle = "bg-button-primary-idle-bg";
      bgColorHover = "hover:bg-button-primary-hover-bg";
      bgColorFocus = "focus:bg-button-primary-focus-bg";
      bgColorActive = "active:bg-button-primary-active-bg";
      bgColorVisited = "visited:bg-button-primary-active-bg";
      bgColorDisabled = "disabled:bg-button-primary-disabled-bg";
      textColorIdle = "text-button-primary-idle-text";
      textColorHover = "hover:text-button-primary-hover-text";
      textColorFocus = "focus:text-button-primary-focus-text";
      textColorActive = "active:text-button-primary-active-text";
      textColorVisited = "visited:text-button-primary-active-text";
      textColorDisabled = "disabled:text-button-primary-disabled-text";
    } else {
      bgColorIdle = "bg-button-secondary-idle-bg";
      bgColorHover = "hover:bg-button-secondary-hover-bg";
      bgColorFocus = "focus:bg-button-secondary-focus-bg";
      bgColorActive = "active:bg-button-secondary-active-bg";
      bgColorVisited = "visited:bg-button-secondary-active-bg";
      bgColorDisabled = "disabled:bg-button-secondary-disabled-bg";
      textColorIdle = "text-button-secondary-idle-text";
      textColorHover = "hover:text-button-secondary-hover-text";
      textColorFocus = "focus:text-button-secondary-focus-text";
      textColorActive = "active:text-button-secondary-active-text";
      textColorVisited = "visited:text-button-secondary-active-text";
      textColorDisabled = "disabled:text-button-secondary-disabled-text";
    }
  } else {
    if (isPrimary) {
      bgColorIdle = "bg-primary-main";
      bgColorHover = "hover:bg-blue-400";
      textColorIdle = "text-white";
    } else {
      border = "border";
      bgColorIdle = "bg-white";
      bgColorHover = "hover:bg-gray-200";
      textColorIdle = "text-blue-text";
    }
  }

  return (
    <Link
      aria-disabled={disabled}
      href={!disabled && link ? link : "#"}
      className={`
        box-border
        inline-block
        w-fit
        rounded-full
        ${disabled ? "pointer-events-none" : ""}
        ${border}
        ${bgColorIdle}
        ${bgColorHover}
        ${bgColorFocus}
        ${bgColorActive}
        ${bgColorVisited}
        ${bgColorDisabled}
        ${textColorIdle}
        ${textColorHover}
        ${textColorFocus}
        ${textColorActive}
        ${textColorVisited}
        ${textColorDisabled}
        ${!snug ? "px-10" : "px-6 leading-tight"}
        py-3
        ${className}`}
      onClick={!disabled && onClick ? onClick : undefined}
      {...rest}
    >
      {bold ? <strong>{content}</strong> : <>{content}</>}
    </Link>
  );
}
