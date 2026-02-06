"use client";

import React, { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import type { RootState } from "@/lib/jobseekerStore";
import { useSelector, useDispatch } from "react-redux";
import InputTextWithLabel from "@/app/ui/components/InputTextWithLabel";
import SelectOptionsWithLabel from "@/app/ui/components/SelectOptionsWithLabel";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import AvatarUpload from "@/app/ui/components/AvatarUpload";
import PillButton from "@/app/ui/components/PillButton";

import { devLog } from "@/app/lib/utils";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import dayjs, { Dayjs } from "dayjs";
import { useSession } from "next-auth/react";
import { useUpdateSession } from "@/app/lib/auth/useUpdateSession";
import {
  JsIntroDTO,
  JsIntroPostDTO,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import {
  setIntroduction,
  initialState,
} from "@/lib/features/profileCreation/jobseekerSlice";
import {
  setPageDirty,
  setPageSaved,
} from "@/lib/features/profileCreation/saveSlice";
import _ from "lodash";
import RequiredTooltip from "@/app/ui/components/mui/RequiredTooltip";
import dynamic from "next/dynamic";
import { Skeleton } from "@mui/material";
const ResumeUploader = dynamic(
  () =>
    import("@/app/ui/components/AIResumeUploader").then(
      (mod) => mod.ResumeUploader,
    ),
  {
    ssr: false,
    loading: () => (
      <div>
        <Skeleton variant="rectangular" width={200} height={40} />
      </div>
    ),
  },
);

const formNamePrefix = "profile-creation-intro-";

export default function CreateJobseekerProfileIntroPage() {
  const dispatch = useDispatch();
  const router = useRouter();
  const { data: session, status } = useSession(); // Use useSession hook to get session and status
  const updateSessionProperties = useUpdateSession();
  const introStoreData = useSelector(
    (state: RootState) => state.jobseeker.introduction,
  );
  const [error, setError] = useState<string | null>(null); // eslint-disable-line @typescript-eslint/no-unused-vars

  const [hasUnmetRequired, setHasUnmetRequired] = useState("");

  const [introData, setIntroData] = useState<JsIntroPostDTO>({
    ...introStoreData,
  });

  const [birthdate, setBirthdate] = useState<Dayjs | null>(
    !Boolean(introData.birthDate) ? null : dayjs(introData.birthDate),
  );

  const [avatarUrl, setAvatarUrl] = useState<string | null>(
    introData.photoUrl ?? null,
  );
  const pathname = usePathname(); // Gets the current pathname

  useEffect(() => {
    if (!session?.user?.id) return;

    if (status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(introStoreData, initialState.introduction)) {
          const { id, firstName, lastName, email } = session.user;

          try {
            devLog("fetching fresh");
            const response = await fetch(
              `/api/jobseekers/account/introduction/get/${session.user.id}`,
            );

            if (!response.ok) {
              setIntroData({
                ...introData,
                userId: id!,
                email: email!,
                firstName: firstName ?? "",
                lastName: lastName ?? "",
                photoUrl: session.user?.image ?? "",
                phoneCountryCode: "United States +1",
              });
              setAvatarUrl(session.user?.image ?? null);
            } else {
              const fetchedData: JsIntroDTO = (await response.json()).result
                .loadIntroPage;
              setIntroData({
                ...introData,
                userId: id!,
                email: email!,
                firstName: firstName ?? "",
                lastName: lastName ?? "",
                CareerPrepAssessment: {
                  streetAddress: fetchedData.CareerPrepAssessment.streetAddress,
                  pronouns: fetchedData.CareerPrepAssessment.pronouns ?? "",
                },
                photoUrl: fetchedData.photoUrl ?? session.user?.image,
                birthDate: fetchedData.birthDate ?? null,
                zipCode: fetchedData.zipCode ?? "",
                city: fetchedData.city,
                county: fetchedData.county,
                currentJobTitle: fetchedData.currentJobTitle,
                introHeadline: fetchedData.introHeadline,
                phone: fetchedData.phone,
                phoneCountryCode: fetchedData.phoneCountryCode,
                state: fetchedData.state,
              });
              setAvatarUrl(fetchedData.photoUrl ?? session.user?.image ?? null);
              setBirthdate(
                !Boolean(fetchedData.birthDate)
                  ? null
                  : dayjs(fetchedData.birthDate),
              );
            }
          } catch (error) {
            console.error(error);
          }
        } else {
          devLog("fetching from store");
        }
      };

      dispatch(setPageSaved("introduction"));
      initializeFormFields();
    }
  }, [session?.user?.id, pathname]); //using pathname as a dependency to trigger useEffect when user clicks back button.

  const handleFieldChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    console.log(e.target);
    const { name, value } = e.target;
    const fieldName = name.substring(formNamePrefix.length);
    if (fieldName.includes(".")) {
      const [nestedObjKey, nestedFieldKey] = fieldName.split(".");
      if (nestedObjKey === "CareerPrepAssessment") {
        setIntroData((prevData) => ({
          ...prevData,
          CareerPrepAssessment: {
            ...prevData.CareerPrepAssessment,
            [nestedFieldKey]: value,
          },
        }));
      }
    } else {
      // Top-level field update
      setIntroData({
        ...introData,
        [fieldName]: value,
      });
    }
    dispatch(setPageDirty("introduction"));
  };

  const handleExtractionComplete = async (jsonData: any) => {
    if (typeof jsonData?.resumeText !== "string") {
      console.error("Error: jsonData.resumeText is missing or not a string.");
      return;
    }

    let resumeData;
    try {
      resumeData = JSON.parse(jsonData.resumeText);
    } catch (parseError) {
      console.error("Error parsing resume JSON:", parseError);
      return;
    }

    try {
      const response = await fetch("/api/jobseekers/account/ai/upsert", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(resumeData),
      });

      if (!response.ok) {
        let errorDetails = `API Error: ${response.status} ${response.statusText}`;
        try {
          const errorResponse = await response.json();
          errorDetails = errorResponse.error || errorDetails;
          console.error("API Error Response:", errorResponse);
        } catch {
          console.error("Could not parse error response body.");
        }
        throw new Error(errorDetails);
      }
      const result = await response.json();
      setIntroData({
        ...introData,
        firstName: result.introduction.firstName ?? "",
        lastName: result.introduction.lastName ?? "",
        phone: result.introduction.phoneNumber ?? "",
      });
      await updateSessionProperties({
        firstName: result.introduction.firstName ?? "",
        lastName: result.introduction.lastName ?? "",
        phone: result.introduction.phoneNumber ?? "",
      });
      devLog("API Upsert Success:", result);
    } catch (apiError: any) {
      console.error("Failed to upsert profile:", apiError);
    } finally {
    }
  };

  const handleImageUpload = (url: string) => {
    // Update the local state with the uploaded image URL
    updateSessionProperties({
      image: url,
    })
      .then(() => {
        setAvatarUrl(url);
        setIntroData({
          ...introData,
          photoUrl: url,
        });
        dispatch(setPageDirty("introduction"));
      })
      .catch((error) =>
        console.error("Failed to update session image:", error),
      );
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }

    setHasUnmetRequired("");

    const updatedIntroData: JsIntroPostDTO = {
      ...introData,
      birthDate: birthdate?.toISOString() ?? null,
      photoUrl: avatarUrl,
    };
    setIntroData(updatedIntroData);

    if (!birthdate || !birthdate.isValid()) {
      setHasUnmetRequired(`${session.user.id}-birthDate`);
      return;
    }

    // Extract firstName, lastName, and name from Redux state fields
    const firstName = introData.firstName;
    const lastName = introData.lastName;
    const name = `${firstName} ${lastName}`;

    try {
      const response = await fetch(
        "/api/jobseekers/account/introduction/upsert",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            ...updatedIntroData,
            userId: session.user.id, // Ensure userId is passed from session
          }),
        },
      );

      if (response.ok) {
        await response.json();

        // Update the redux state
        dispatch(setPageSaved("introduction"));
        dispatch(setIntroduction(updatedIntroData));

        // Update session properties using the custom hook
        await updateSessionProperties({
          firstName,
          lastName,
          name,
          image: updatedIntroData.photoUrl,
        });

        router.push("/edit-profile/jobseeker/preferences");
      } else {
        const errorMessage = `Failed to submit basic info. Status: ${response.status} - ${response.statusText}`;
        setError(errorMessage);
      }
    } catch (e: any) {
      setError(`An unexpected error occurred: ${e.message}`);
    }
  };

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(1 / 6) * 100} />
        <p>Step 1/6</p>
        <h1>Profile Settings</h1>
        <p className="subtitle">* Indicates a required field</p>

        <form onSubmit={handleSubmit}>
          <fieldset>
            <legend>
              <h2>Profile autofill</h2>
            </legend>
            <ResumeUploader
              onExtractionCompleteAction={handleExtractionComplete}
            />
          </fieldset>
          <fieldset>
            <legend>
              <h2>Avatar</h2>
            </legend>
            <AvatarUpload
              id="profile-creation-intro-avatar-upload"
              fileTypeText="File types: SVG, PNG, JPG, GIF, or WEBP"
              accept=".svg,.png,.jpg,.jpeg,.gif,.webp"
              maxSizeMB={5}
              userId={session?.user?.id!}
              onImageUpload={handleImageUpload}
              initialImageUrl={session?.user?.image || introData.photoUrl || ""}
              apiPath="/api/users/avatar/upload"
            />
          </fieldset>
          <fieldset>
            <legend>
              <h2>Contact Information</h2>
            </legend>

            <div className="profile-form-grid md:grid-cols-2">
              <InputTextWithLabel
                id="profile-creation-intro-firstName"
                placeholder="Your first name"
                onChange={handleFieldChange}
                value={introData.firstName ?? ""}
              >
                First Name *
              </InputTextWithLabel>
              <InputTextWithLabel
                id="profile-creation-intro-lastName"
                placeholder="Your last name"
                onChange={handleFieldChange}
                value={introData.lastName ?? ""}
              >
                Last Name *
              </InputTextWithLabel>

              <InputTextWithLabel
                id="profile-creation-intro-CareerPrepAssessment.pronouns"
                placeholder="They/Them"
                onChange={handleFieldChange}
                value={
                  introData.CareerPrepAssessment
                    ? (introData.CareerPrepAssessment.pronouns ?? "")
                    : ""
                }
              >
                Preferred Pronouns
              </InputTextWithLabel>
            </div>

            <div className="profile-form-grid">
              <RequiredTooltip
                open={
                  hasUnmetRequired === `${introData.userId}-birthDate` &&
                  !Boolean(birthdate)
                }
                errorMessage="Your birth date is required"
              >
                <DatePicker
                  label="Birth Date *"
                  value={birthdate}
                  onChange={(val) => {
                    setBirthdate(val?.isValid() ? val : null);
                  }}
                  slotProps={{ textField: { fullWidth: true } }}
                />
              </RequiredTooltip>
            </div>

            <div className="profile-form-grid">
              <InputTextWithLabel
                id="profile-creation-intro-CareerPrepAssessment.streetAddress"
                placeholder="1234 N Stroodle Ave"
                onChange={handleFieldChange}
                value={
                  introData.CareerPrepAssessment &&
                  (introData.CareerPrepAssessment.streetAddress ?? undefined)
                }
              >
                Street Address
              </InputTextWithLabel>
            </div>

            <div className="profile-form-grid md:grid-cols-2">
              <InputTextWithLabel
                id="profile-creation-intro-zipCode"
                placeholder="Zipcode"
                onChange={handleFieldChange}
                value={introData.zipCode ?? ""}
                pattern="\d{5}(-\d{4})?"
                required
              >
                Zip Code
              </InputTextWithLabel>
            </div>

            <div className="profile-form-grid">
              <InputTextWithLabel
                type="email"
                id="profile-creation-intro-email"
                onChange={handleFieldChange}
                placeholder="example@example.com"
                value={introData.email ?? ""}
                required
                disabled
              >
                Email
              </InputTextWithLabel>
            </div>

            <div className="profile-form-grid tablet:grid-cols-2">
              <SelectOptionsWithLabel
                id="profile-creation-intro-phoneCountryCode"
                onChange={handleFieldChange}
                options={[
                  { label: "Afghanistan +93", value: "Afghanistan +93" },
                  { label: "Albania +355", value: "Albania +355" },
                  { label: "Algeria +213", value: "Algeria +213" },
                  {
                    label: "American Samoa +1-684",
                    value: "American Samoa +1-684",
                  },
                  { label: "Andorra +376", value: "Andorra +376" },
                  { label: "Angola +244", value: "Angola +244" },
                  { label: "Anguilla +1-264", value: "Anguilla +1-264" },
                  { label: "Antarctica +672", value: "Antarctica +672" },
                  {
                    label: "Antigua and Barbuda +1-268",
                    value: "Antigua and Barbuda +1-268",
                  },
                  { label: "Argentina +54", value: "Argentina +54" },
                  { label: "Armenia +374", value: "Armenia +374" },
                  { label: "Aruba +297", value: "Aruba +297" },
                  { label: "Australia +61", value: "Australia +61" },
                  { label: "Austria +43", value: "Austria +43" },
                  { label: "Azerbaijan +994", value: "Azerbaijan +994" },
                  { label: "Bahamas +1-242", value: "Bahamas +1-242" },
                  { label: "Bahrain +973", value: "Bahrain +973" },
                  { label: "Bangladesh +880", value: "Bangladesh +880" },
                  { label: "Barbados +1-246", value: "Barbados +1-246" },
                  { label: "Belarus +375", value: "Belarus +375" },
                  { label: "Belgium +32", value: "Belgium +32" },
                  { label: "Belize +501", value: "Belize +501" },
                  { label: "Benin +229", value: "Benin +229" },
                  { label: "Bermuda +1-441", value: "Bermuda +1-441" },
                  { label: "Bhutan +975", value: "Bhutan +975" },
                  { label: "Bolivia +591", value: "Bolivia +591" },
                  {
                    label: "Bosnia and Herzegovina +387",
                    value: "Bosnia and Herzegovina +387",
                  },
                  { label: "Botswana +267", value: "Botswana +267" },
                  { label: "Brazil +55", value: "Brazil +55" },
                  {
                    label: "British Indian Ocean Territory +246",
                    value: "British Indian Ocean Territory +246",
                  },
                  {
                    label: "British Virgin Islands +1-284",
                    value: "British Virgin Islands +1-284",
                  },
                  { label: "Brunei +673", value: "Brunei +673" },
                  { label: "Bulgaria +359", value: "Bulgaria +359" },
                  { label: "Burkina Faso +226", value: "Burkina Faso +226" },
                  { label: "Burundi +257", value: "Burundi +257" },
                  { label: "Cambodia +855", value: "Cambodia +855" },
                  { label: "Cameroon +237", value: "Cameroon +237" },
                  { label: "Canada +1", value: "Canada +1" },
                  { label: "Cape Verde +238", value: "Cape Verde +238" },
                  {
                    label: "Cayman Islands +1-345",
                    value: "Cayman Islands +1-345",
                  },
                  {
                    label: "Central African Republic +236",
                    value: "Central African Republic +236",
                  },
                  { label: "Chad +235", value: "Chad +235" },
                  { label: "Chile +56", value: "Chile +56" },
                  { label: "China +86", value: "China +86" },
                  {
                    label: "Christmas Island +61",
                    value: "Christmas Island +61",
                  },
                  { label: "Cocos Islands +61", value: "Cocos Islands +61" },
                  { label: "Colombia +57", value: "Colombia +57" },
                  { label: "Comoros +269", value: "Comoros +269" },
                  { label: "Cook Islands +682", value: "Cook Islands +682" },
                  { label: "Costa Rica +506", value: "Costa Rica +506" },
                  { label: "Croatia +385", value: "Croatia +385" },
                  { label: "Cuba +53", value: "Cuba +53" },
                  { label: "Curacao +599", value: "Curacao +599" },
                  { label: "Cyprus +357", value: "Cyprus +357" },
                  {
                    label: "Czech Republic +420",
                    value: "Czech Republic +420",
                  },
                  {
                    label: "Democratic Republic of the Congo +243",
                    value: "Democratic Republic of the Congo +243",
                  },
                  { label: "Denmark +45", value: "Denmark +45" },
                  { label: "Djibouti +253", value: "Djibouti +253" },
                  { label: "Dominica +1-767", value: "Dominica +1-767" },
                  {
                    label: "Dominican Republic +1-809",
                    value: "Dominican Republic +1-809",
                  },
                  {
                    label: "Dominican Republic +1-829",
                    value: "Dominican Republic +1-829",
                  },
                  {
                    label: "Dominican Republic +1-849",
                    value: "Dominican Republic +1-849",
                  },
                  { label: "East Timor +670", value: "East Timor +670" },
                  { label: "Ecuador +593", value: "Ecuador +593" },
                  { label: "Egypt +20", value: "Egypt +20" },
                  { label: "El Salvador +503", value: "El Salvador +503" },
                  {
                    label: "Equatorial Guinea +240",
                    value: "Equatorial Guinea +240",
                  },
                  { label: "Eritrea +291", value: "Eritrea +291" },
                  { label: "Estonia +372", value: "Estonia +372" },
                  { label: "Ethiopia +251", value: "Ethiopia +251" },
                  {
                    label: "Falkland Islands +500",
                    value: "Falkland Islands +500",
                  },
                  { label: "Faroe Islands +298", value: "Faroe Islands +298" },
                  { label: "Fiji +679", value: "Fiji +679" },
                  { label: "Finland +358", value: "Finland +358" },
                  { label: "France +33", value: "France +33" },
                  {
                    label: "French Polynesia +689",
                    value: "French Polynesia +689",
                  },
                  { label: "Gabon +241", value: "Gabon +241" },
                  { label: "Gambia +220", value: "Gambia +220" },
                  { label: "Georgia +995", value: "Georgia +995" },
                  { label: "Germany +49", value: "Germany +49" },
                  { label: "Ghana +233", value: "Ghana +233" },
                  { label: "Gibraltar +350", value: "Gibraltar +350" },
                  { label: "Greece +30", value: "Greece +30" },
                  { label: "Greenland +299", value: "Greenland +299" },
                  { label: "Grenada +1-473", value: "Grenada +1-473" },
                  { label: "Guam +1-671", value: "Guam +1-671" },
                  { label: "Guatemala +502", value: "Guatemala +502" },
                  { label: "Guernsey +44-1481", value: "Guernsey +44-1481" },
                  { label: "Guinea +224", value: "Guinea +224" },
                  { label: "Guinea-Bissau +245", value: "Guinea-Bissau +245" },
                  { label: "Guyana +592", value: "Guyana +592" },
                  { label: "Haiti +509", value: "Haiti +509" },
                  { label: "Honduras +504", value: "Honduras +504" },
                  { label: "Hong Kong +852", value: "Hong Kong +852" },
                  { label: "Hungary +36", value: "Hungary +36" },
                  { label: "Iceland +354", value: "Iceland +354" },
                  { label: "India +91", value: "India +91" },
                  { label: "Indonesia +62", value: "Indonesia +62" },
                  { label: "Iran +98", value: "Iran +98" },
                  { label: "Iraq +964", value: "Iraq +964" },
                  { label: "Ireland +353", value: "Ireland +353" },
                  {
                    label: "Isle of Man +44-1624",
                    value: "Isle of Man +44-1624",
                  },
                  { label: "Israel +972", value: "Israel +972" },
                  { label: "Italy +39", value: "Italy +39" },
                  { label: "Ivory Coast +225", value: "Ivory Coast +225" },
                  { label: "Jamaica +1-876", value: "Jamaica +1-876" },
                  { label: "Japan +81", value: "Japan +81" },
                  { label: "Jersey +44-1534", value: "Jersey +44-1534" },
                  { label: "Jordan +962", value: "Jordan +962" },
                  { label: "Kazakhstan +7", value: "Kazakhstan +7" },
                  { label: "Kenya +254", value: "Kenya +254" },
                  { label: "Kiribati +686", value: "Kiribati +686" },
                  { label: "Kosovo +383", value: "Kosovo +383" },
                  { label: "Kuwait +965", value: "Kuwait +965" },
                  { label: "Kyrgyzstan +996", value: "Kyrgyzstan +996" },
                  { label: "Laos +856", value: "Laos +856" },
                  { label: "Latvia +371", value: "Latvia +371" },
                  { label: "Lebanon +961", value: "Lebanon +961" },
                  { label: "Lesotho +266", value: "Lesotho +266" },
                  { label: "Liberia +231", value: "Liberia +231" },
                  { label: "Libya +218", value: "Libya +218" },
                  { label: "Liechtenstein +423", value: "Liechtenstein +423" },
                  { label: "Lithuania +370", value: "Lithuania +370" },
                  { label: "Luxembourg +352", value: "Luxembourg +352" },
                  { label: "Macau +853", value: "Macau +853" },
                  { label: "Macedonia +389", value: "Macedonia +389" },
                  { label: "Madagascar +261", value: "Madagascar +261" },
                  { label: "Malawi +265", value: "Malawi +265" },
                  { label: "Malaysia +60", value: "Malaysia +60" },
                  { label: "Maldives +960", value: "Maldives +960" },
                  { label: "Mali +223", value: "Mali +223" },
                  { label: "Malta +356", value: "Malta +356" },
                  {
                    label: "Marshall Islands +692",
                    value: "Marshall Islands +692",
                  },
                  { label: "Mauritania +222", value: "Mauritania +222" },
                  { label: "Mauritius +230", value: "Mauritius +230" },
                  { label: "Mayotte +262", value: "Mayotte +262" },
                  { label: "Mexico +52", value: "Mexico +52" },
                  { label: "Micronesia +691", value: "Micronesia +691" },
                  { label: "Moldova +373", value: "Moldova +373" },
                  { label: "Monaco +377", value: "Monaco +377" },
                  { label: "Mongolia +976", value: "Mongolia +976" },
                  { label: "Montenegro +382", value: "Montenegro +382" },
                  { label: "Montserrat +1-664", value: "Montserrat +1-664" },
                  { label: "Morocco +212", value: "Morocco +212" },
                  { label: "Mozambique +258", value: "Mozambique +258" },
                  { label: "Myanmar +95", value: "Myanmar +95" },
                  { label: "Namibia +264", value: "Namibia +264" },
                  { label: "Nauru +674", value: "Nauru +674" },
                  { label: "Nepal +977", value: "Nepal +977" },
                  { label: "Netherlands +31", value: "Netherlands +31" },
                  {
                    label: "Netherlands Antilles +599",
                    value: "Netherlands Antilles +599",
                  },
                  { label: "New Caledonia +687", value: "New Caledonia +687" },
                  { label: "New Zealand +64", value: "New Zealand +64" },
                  { label: "Nicaragua +505", value: "Nicaragua +505" },
                  { label: "Niger +227", value: "Niger +227" },
                  { label: "Nigeria +234", value: "Nigeria +234" },
                  { label: "Niue +683", value: "Niue +683" },
                  { label: "North Korea +850", value: "North Korea +850" },
                  {
                    label: "Northern Mariana Islands +1-670",
                    value: "Northern Mariana Islands +1-670",
                  },
                  { label: "Norway +47", value: "Norway +47" },
                  { label: "Oman +968", value: "Oman +968" },
                  { label: "Pakistan +92", value: "Pakistan +92" },
                  { label: "Palau +680", value: "Palau +680" },
                  { label: "Palestine +970", value: "Palestine +970" },
                  { label: "Panama +507", value: "Panama +507" },
                  {
                    label: "Papua New Guinea +675",
                    value: "Papua New Guinea +675",
                  },
                  { label: "Paraguay +595", value: "Paraguay +595" },
                  { label: "Peru +51", value: "Peru +51" },
                  { label: "Philippines +63", value: "Philippines +63" },
                  { label: "Pitcairn +64", value: "Pitcairn +64" },
                  { label: "Poland +48", value: "Poland +48" },
                  { label: "Portugal +351", value: "Portugal +351" },
                  { label: "Puerto Rico +1-787", value: "Puerto Rico +1-787" },
                  { label: "Puerto Rico +1-939", value: "Puerto Rico +1-939" },
                  { label: "Qatar +974", value: "Qatar +974" },
                  {
                    label: "Republic of the Congo +242",
                    value: "Republic of the Congo +242",
                  },
                  { label: "Reunion +262", value: "Reunion +262" },
                  { label: "Romania +40", value: "Romania +40" },
                  { label: "Russia +7", value: "Russia +7" },
                  { label: "Rwanda +250", value: "Rwanda +250" },
                  {
                    label: "Saint Barthelemy +590",
                    value: "Saint Barthelemy +590",
                  },
                  { label: "Saint Helena +290", value: "Saint Helena +290" },
                  {
                    label: "Saint Kitts and Nevis +1-869",
                    value: "Saint Kitts and Nevis +1-869",
                  },
                  { label: "Saint Lucia +1-758", value: "Saint Lucia +1-758" },
                  { label: "Saint Martin +590", value: "Saint Martin +590" },
                  {
                    label: "Saint Pierre and Miquelon +508",
                    value: "Saint Pierre and Miquelon +508",
                  },
                  {
                    label: "Saint Vincent and the Grenadines +1-784",
                    value: "Saint Vincent and the Grenadines +1-784",
                  },
                  { label: "Samoa +685", value: "Samoa +685" },
                  { label: "San Marino +378", value: "San Marino +378" },
                  {
                    label: "Sao Tome and Principe +239",
                    value: "Sao Tome and Principe +239",
                  },
                  { label: "Saudi Arabia +966", value: "Saudi Arabia +966" },
                  { label: "Senegal +221", value: "Senegal +221" },
                  { label: "Serbia +381", value: "Serbia +381" },
                  { label: "Seychelles +248", value: "Seychelles +248" },
                  { label: "Sierra Leone +232", value: "Sierra Leone +232" },
                  { label: "Singapore +65", value: "Singapore +65" },
                  {
                    label: "Sint Maarten +1-721",
                    value: "Sint Maarten +1-721",
                  },
                  { label: "Slovakia +421", value: "Slovakia +421" },
                  { label: "Slovenia +386", value: "Slovenia +386" },
                  {
                    label: "Solomon Islands +677",
                    value: "Solomon Islands +677",
                  },
                  { label: "Somalia +252", value: "Somalia +252" },
                  { label: "South Africa +27", value: "South Africa +27" },
                  { label: "South Korea +82", value: "South Korea +82" },
                  { label: "South Sudan +211", value: "South Sudan +211" },
                  { label: "Spain +34", value: "Spain +34" },
                  { label: "Sri Lanka +94", value: "Sri Lanka +94" },
                  { label: "Sudan +249", value: "Sudan +249" },
                  { label: "Suriname +597", value: "Suriname +597" },
                  {
                    label: "Svalbard and Jan Mayen +47",
                    value: "Svalbard and Jan Mayen +47",
                  },
                  { label: "Swaziland +268", value: "Swaziland +268" },
                  { label: "Sweden +46", value: "Sweden +46" },
                  { label: "Switzerland +41", value: "Switzerland +41" },
                  { label: "Syria +963", value: "Syria +963" },
                  { label: "Taiwan +886", value: "Taiwan +886" },
                  { label: "Tajikistan +992", value: "Tajikistan +992" },
                  { label: "Tanzania +255", value: "Tanzania +255" },
                  { label: "Thailand +66", value: "Thailand +66" },
                  { label: "Togo +228", value: "Togo +228" },
                  { label: "Tokelau +690", value: "Tokelau +690" },
                  { label: "Tonga +676", value: "Tonga +676" },
                  {
                    label: "Trinidad and Tobago +1-868",
                    value: "Trinidad and Tobago +1-868",
                  },
                  { label: "Tunisia +216", value: "Tunisia +216" },
                  { label: "Turkey +90", value: "Turkey +90" },
                  { label: "Turkmenistan +993", value: "Turkmenistan +993" },
                  {
                    label: "Turks and Caicos Islands +1-649",
                    value: "Turks and Caicos Islands +1-649",
                  },
                  { label: "Tuvalu +688", value: "Tuvalu +688" },
                  {
                    label: "U.S. Virgin Islands +1-340",
                    value: "U.S. Virgin Islands +1-340",
                  },
                  { label: "Uganda +256", value: "Uganda +256" },
                  { label: "Ukraine +380", value: "Ukraine +380" },
                  {
                    label: "United Arab Emirates +971",
                    value: "United Arab Emirates +971",
                  },
                  { label: "United Kingdom +44", value: "United Kingdom +44" },
                  { label: "United States +1", value: "United States +1" },
                  { label: "Uruguay +598", value: "Uruguay +598" },
                  { label: "Uzbekistan +998", value: "Uzbekistan +998" },
                  { label: "Vanuatu +678", value: "Vanuatu +678" },
                  { label: "Vatican +379", value: "Vatican +379" },
                  { label: "Venezuela +58", value: "Venezuela +58" },
                  { label: "Vietnam +84", value: "Vietnam +84" },
                  {
                    label: "Wallis and Futuna +681",
                    value: "Wallis and Futuna +681",
                  },
                  {
                    label: "Western Sahara +212",
                    value: "Western Sahara +212",
                  },
                  { label: "Yemen +967", value: "Yemen +967" },
                  { label: "Zambia +260", value: "Zambia +260" },
                  { label: "Zimbabwe +263", value: "Zimbabwe +263" },
                ]}
                value={introData.phoneCountryCode ?? "United States +1"}
              >
                Country Phone Code
              </SelectOptionsWithLabel>
              <InputTextWithLabel
                id="profile-creation-intro-phone"
                type="tel"
                placeholder="Phone number"
                onChange={handleFieldChange}
                value={introData.phone ?? ""}
              >
                Phone Number
              </InputTextWithLabel>
            </div>
          </fieldset>

          <div className="profile-form-progress-btn-single-end">
            {/* <Button variant="outlined">
              Cancel
            </Button> */}
            <PillButton type="submit">Save and continue</PillButton>
          </div>
        </form>
      </section>
    </main>
  );
}
