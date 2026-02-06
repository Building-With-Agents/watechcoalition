"use client";

import React, { useEffect } from "react";
import Confetti from "@/app/ui/components/Confetti";

import PillButton from "@/app/ui/components/PillButton";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function CreateJobseekerProfilePreferencesPage() {
  const router = useRouter();
  const { data: session, status } = useSession();

  useEffect(() => {
    if (status === "authenticated" && session?.user?.jobseekerId) {
      const fetchData = async () => {
        try {
          const response = await fetch(`/api/jobseekers/validate-profile`, {
            method: "PATCH", // Specify the PATCH method
            headers: {
              "Content-Type": "application/json", // Set the content type
            },
          });
          if (!response.ok) {
            throw new Error("Failed to validate jobseeker profile.");
          }
        } catch (error) {
          console.error("Error fetching jobseeker preferences:", error);
        }
      };
      fetchData();
    }
  }, [status, session]);
  function handleClick() {
    router.push(`/services/jobseekers/dashboard`);
  }
  const firstName = session?.user?.firstName;
  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section main-content">
        <Confetti />
        <h1>Congrats on completing your profile, {firstName}!</h1>

        <p className="subtitle-congrats">{`Let's kickstart your career journey!`}</p>
        <PillButton onClick={handleClick}>Get Started</PillButton>
      </section>
    </main>
  );
}
