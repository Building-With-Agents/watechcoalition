"use client";
import React, { useRef } from "react";
import { Provider } from "react-redux";
import { makeStore, AppStore } from "@/lib/employerStore";
import {
  EmployerState,
  setPersonal,
} from "@/lib/features/profileCreation/employerSlice";

interface Props {
  employer?: EmployerState | null;
  children: React.ReactNode;
}

export default function StoreProvider({ employer = null, children }: Props) {
  const storeRef = useRef<AppStore>(null);
  if (!storeRef.current) {
    // Create the store instance the first time this renders
    storeRef.current = makeStore();
    if (employer !== null) {
      storeRef.current.dispatch(setPersonal(employer.personal));
    }
  }

  return <Provider store={storeRef.current}>{children}</Provider>;
}
