"use client";

import React, { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { RootState } from "@/lib/employerStore";
import { useSelector, useDispatch } from "react-redux";
// import { addField, updateField, submitForm, submitFormSuccess, submitFormFailure, FormState } from '@/lib/features/profileCreation/formSlice';
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import PillButton from "@/app/ui/components/PillButton";
import TextareaWithLabel from "@/app/ui/components/TextareaWithLabel";
import { useSession } from "next-auth/react";
import { PostEmployerMissionDTO } from "@/data/dtos/EmployerProfileCreationDTOs";
import {
  setMission,
  initialState,
} from "@/lib/features/profileCreation/employerSlice";
import {
  setPageDirty,
  setPageSaved,
} from "@/lib/features/profileCreation/saveSlice";
import _ from "lodash";
import { devLog } from "@/app/lib/utils";
import { ReadEmployerRecordDTO } from "@/app/lib/employer";

const formNamePrefix = "profile-creation-company-mission-";

export default function CreateEmployerCompanyInfoMissionPage() {
  const missionStoreData = useSelector(
    (state: RootState) => state.employer.mission,
  );
  const [missionData, setMissionData] = useState<PostEmployerMissionDTO>({
    ...missionStoreData,
  });
  const [employerInfo, setEmployerInfo] = useState<ReadEmployerRecordDTO>();

  const dispatch = useDispatch();
  const router = useRouter();

  const { data: session, status } = useSession();

  // get employers.is_verified_employee
  useEffect(() => {
    fetch("/api/employers/account/profile/get")
      .then((res) => {
        return res.json();
      })
      .then((jsonData) => {
        setEmployerInfo(jsonData);
      });
  }, []);

  useEffect(() => {
    const initializeFormFields = async () => {
      console.log("session", session);
      if (!session?.user.id) return;
      if (status === "authenticated") {
        if (_.isEqual(missionStoreData, initialState.mission)) {
          try {
            const response = await fetch(
              `/api/companies/mission/get/${session.user.companyId}`,
              {
                method: "GET",
                headers: {
                  "Content-Type": "application/json",
                },
              },
            );

            if (!response.ok) {
              await response.json();
            } else {
              const { result } = await response.json();

              console.log("fetchedData", result);
              setMissionData({
                ...missionData,
                // companyId: result.companyId,
                mission: result.mission ?? "",
              });
            }
          } catch {}
        } else {
          console.log("fetching from redux store");
        }
      }
    };
    initializeFormFields();
    dispatch(setPageSaved("mission"));
    devLog(missionData);
  }, [session?.user?.id]);

  const handleFieldChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    console.log(name, value);
    dispatch(setPageDirty("mission"));
    const fieldName = name.substring(formNamePrefix.length);
    console.log("fieldName", fieldName);
    if (missionData.hasOwnProperty(fieldName)) {
      missionData[fieldName as keyof PostEmployerMissionDTO] = value;
      setMissionData({ ...missionData });
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!session || !session.user) {
      console.error("User session is not available.");
      return;
    }
    setMissionData({ ...missionData });
    devLog("missionData", missionData);

    try {
      const response = await fetch("/api/companies/mission/update/", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(missionData),
      });

      if (response.ok) {
        await response.json();
        dispatch(setPageSaved("mission"));
        dispatch(setMission(missionData));
        router.push("/edit-profile/employer/video");
      } else {
        await response.json();
        if (!session?.user?.employeeIsApproved)
          router.push("/edit-profile/employer/video");
      }
    } catch {}
  };

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(4 / 5) * 100} />
        <p>Step 4/5</p>
        <h1>Company Info</h1>
        <p className="subtitle">* Indicates a required field</p>
        <h2>Mission</h2>

        <form onSubmit={handleSubmit}>
          What is your company mission *
          <div className="profile-form-grid">
            <fieldset>
              <TextareaWithLabel
                id="profile-creation-company-mission-mission"
                placeholder="Tell your company mission"
                disabled={!employerInfo?.is_verified_employee}
                rows="16"
                required
                onChange={handleFieldChange}
                value={missionData.mission}
              ></TextareaWithLabel>
            </fieldset>
          </div>
          <div className="profile-form-progress-btn-group">
            <PillButton
              className="custom-outline-btn"
              onClick={() => router.push("/edit-profile/employer/about")}
            >
              Previous
            </PillButton>
            <PillButton type="submit">Save and continue</PillButton>
          </div>
        </form>
      </section>
    </main>
  );
}
