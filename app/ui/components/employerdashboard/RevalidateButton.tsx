"use client";

import { useRouter } from "next/navigation";
/**
 * currnetly unused will refreash current route
 */
export default function RevalidateButton() {
  const router = useRouter();
  return (
    <button
      onClick={() => {
        router.refresh();
      }}
    >
      Updates May Not Be Reflected click here to see the latest information
    </button>
  );
}
