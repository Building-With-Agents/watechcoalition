"use client";
import { signOut, useSession } from "next-auth/react";
import { useEffect } from "react";

export default function SignOutPage() {
  const { status } = useSession();

  useEffect(() => {
    if (status === "authenticated") signOut({ redirectTo: "/" });
  }, [status]);

  return <></>;
}
