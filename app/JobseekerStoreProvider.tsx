"use client";
import React, { useRef } from "react";
import { Provider } from "react-redux";
import { makeStore, AppStore } from "@/lib/jobseekerStore";
import {
  JobseekerState,
  setDisclosures,
  setEducation,
  setIntroduction,
  setPreferences,
  setShowcase,
  setWorkExperience,
} from "@/lib/features/profileCreation/jobseekerSlice";

interface Props {
  jobseeker?: JobseekerState | null;
  children: React.ReactNode;
}

export default function StoreProvider({ jobseeker = null, children }: Props) {
  const storeRef = useRef<AppStore>(null);
  if (!storeRef.current) {
    // Create the store instance the first time this renders
    storeRef.current = makeStore();
    if (jobseeker !== null) {
      storeRef.current.dispatch(setIntroduction(jobseeker.introduction));
      storeRef.current.dispatch(setEducation(jobseeker.education));
      storeRef.current.dispatch(setWorkExperience(jobseeker.workExperience));
      storeRef.current.dispatch(setShowcase(jobseeker.showcase));
      storeRef.current.dispatch(setPreferences(jobseeker.preferences));
      storeRef.current.dispatch(setDisclosures(jobseeker.disclosures));
    }
  }

  return <Provider store={storeRef.current}>{children}</Provider>;
}
