"use client";

import React, { ChangeEvent, FormEvent, useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { useSelector, useDispatch } from "react-redux";
import type { RootState } from "@/lib/employerStore";
import InputTextWithLabel from "@/app/ui/components/InputTextWithLabel";
import SelectOptionsWithLabel from "@/app/ui/components/SelectOptionsWithLabel";
import AvatarUpload from "@/app/ui/components/AvatarUpload";
import PillButton from "@/app/ui/components/PillButton";
import { DatePicker } from "@mui/x-date-pickers";
import SelectAutoload from "@/app/ui/components/mui/SelectAutoload";
import TextFieldWithAutocomplete from "@/app/ui/components/mui/TextFieldWithAutocomplete";
import { useSession } from "next-auth/react";
import { useUpdateSession } from "@/app/lib/auth/useUpdateSession";
import {
  PostAddressDTO,
  PostCompanyInfoDTO,
  ReadAddressDTO,
  ReadCompanyInfoDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";
import { IndustrySectorDropdownDTO } from "@/data/dtos/IndustrySectorDropdownDTO";
import {
  setCompany,
  initialState,
} from "@/lib/features/profileCreation/employerSlice";
import {
  setPageDirty,
  setPageSaved,
} from "@/lib/features/profileCreation/saveSlice";
import dayjs, { Dayjs } from "dayjs";
import _ from "lodash";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import { ReadEmployerRecordDTO } from "@/app/lib/employer";

const formNamePrefix = "profile-creation-company-";

export default function CreateEmployerCompanyInfoPage() {
  const companyStoreData = useSelector(
    (state: RootState) => state.employer.company,
  );
  const [companyData, setCompanyData] = useState<PostCompanyInfoDTO>({
    ...companyStoreData,
  });
  const [yearFounded, setYearFounded] = useState<Dayjs | null>(
    companyData.yearFounded ? dayjs(companyData.yearFounded) : null,
  );
  const [industry, setIndustry] = useState<IndustrySectorDropdownDTO | null>(
    null,
  );
  const [selectedWorkLocation, setSelectedWorkLocation] =
    useState<PostAddressDTO>({
      city: "",
      state: "",
      stateCode: "",
      zip: "",
      county: "",
    });
  const [employerInfo, setEmployerInfo] = useState<ReadEmployerRecordDTO>();

  const dispatch = useDispatch();
  const router = useRouter();
  const pathname = usePathname();
  const { data: session } = useSession();
  const updateSessionProperties = useUpdateSession();

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
    if (!session?.user?.id) return;

    const fetchCompanyData = async (companyId: string) => {
      try {
        const response = await fetch(
          `/api/employers/account/company-info/get/${companyId}`,
        );
        if (!response.ok) {
          console.warn("Data fetching failed. Using initialized fields.");
          return;
        }

        const fetchedData: ReadCompanyInfoDTO = (await response.json()).result;
        const companyZips: PostAddressDTO[] = (
          fetchedData?.companyAddresses || []
        )
          .filter((addr): addr is ReadAddressDTO => addr?.zip !== undefined)
          .map((addr) => ({
            city: addr?.city,
            stateCode: addr?.stateCode,
            zip: addr?.zip!,
          }));
        const updatedCompanyData: PostCompanyInfoDTO = {
          userId: session?.user?.id!,
          employerId: session?.user?.employerId || undefined,
          companyId: fetchedData.companyId || undefined,
          industrySectorId: fetchedData.industrySectorId || undefined,
          industrySectorTitle: fetchedData.industrySectorTitle || undefined,
          companyName: fetchedData.companyName,
          companyAddresses: companyZips,
          logoUrl: fetchedData.logoUrl || undefined,
          aboutUs: fetchedData.aboutUs || undefined,
          companyEmail: fetchedData.companyEmail || "",
          yearFounded: fetchedData.yearFounded || "",
          websiteUrl: fetchedData.websiteUrl || undefined,
          videoUrl: fetchedData.videoUrl || undefined,
          phoneCountryCode: fetchedData.phoneCountryCode || undefined,
          companyPhone: fetchedData.companyPhone || undefined,
          mission: fetchedData.mission || undefined,
          vision: fetchedData.vision || undefined,
          companySize: fetchedData.companySize || "",
          estimatedAnnualHires: fetchedData.estimatedAnnualHires || "",
        };
        setCompanyData(updatedCompanyData);
        setYearFounded(
          fetchedData.yearFounded
            ? dayjs().year(parseInt(fetchedData.yearFounded))
            : null,
        );

        setIndustry({
          industry_sector_id: fetchedData.industrySectorId ?? "",
          sector_title: fetchedData.industrySectorTitle || "",
        });
      } catch {
        console.warn("Error fetching company data. Using initialized fields.");
      }
    };
    // console.log('isEqual', _.isEqual(companyStoreData, initialState.company))
    // have to use session here because employerInfo isn't set yet.
    if (
      _.isEqual(companyStoreData, initialState.company) &&
      session.user.companyId
    ) {
      fetchCompanyData(session.user.companyId ?? "");
      console.log("fetchedCompanyData");
    } else {
      setCompanyData(companyStoreData);
      setYearFounded(
        companyData.yearFounded ? dayjs(companyData.yearFounded) : null,
      );
    }
    dispatch(setPageSaved("company"));
  }, [session?.user.id, pathname]);

  const handleFieldChange = (
    e: ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value } = e.target;
    const fieldName = name.substring(formNamePrefix.length);
    dispatch(setPageDirty("company"));
    // console.log('companyData', companyData)

    if (companyData.hasOwnProperty(fieldName)) {
      setCompanyData((prevState) => ({
        ...prevState,
        [fieldName]: value,
      }));
    }
  };

  const handleAddressSelection = (
    e: React.SyntheticEvent<Element, Event>,
    val: string | ReadAddressDTO | null,
  ) => {
    dispatch(setPageDirty("company"));
    if (val && typeof val === "object" && "zip" in val) {
      setSelectedWorkLocation((prevState) => ({
        ...prevState,
        zip: val.zip!,
      }));

      setCompanyData((prevData) => {
        const alreadyExists = prevData.companyAddresses?.some(
          (location) => location.zip === val.zip,
        );

        if (!alreadyExists) {
          const updatedAddresses = prevData.companyAddresses
            ? [...prevData.companyAddresses, val]
            : [val];
          return {
            ...prevData,
            companyAddresses: updatedAddresses,
          };
        }
        return prevData;
      });
    }
  };

  const handleImageUpload = (url: string) => {
    dispatch(setPageDirty("company"));
    setCompanyData((prevState) => ({
      ...prevState,
      logoUrl: url,
    }));
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    if (!session?.user?.id || !session?.user?.employerId) {
      console.error("User session or required fields are not available.");
      return;
    }
    // console.log('employerInfo', employerInfo)
    const finalCompanyData: PostCompanyInfoDTO = {
      ...companyData,
      userId: employerInfo?.user_id!,
      employerId: employerInfo?.employer_id!,
      companyId: employerInfo?.company_id!,
    };
    try {
      const response = await fetch(
        "/api/employers/account/company-info/upsert",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(finalCompanyData),
        },
      );

      if (response.ok) {
        dispatch(setCompany(finalCompanyData));
        await updateSessionProperties({
          companyId: finalCompanyData.companyId,
        });

        router.push("/edit-profile/employer/about");
        dispatch(setPageSaved("company"));
      } else {
        if (!employerInfo?.is_verified_employee)
          router.push("/edit-profile/employer/about");
        const errorData = await response.json();
        console.error("Failed to update company info:", errorData);
      }
    } catch (error) {
      console.error("Error updating company info:", error);
    }
  };

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section">
        <ProgressBarFlat progress={(2 / 5) * 100} />
        <p className="mb-6">Step 2/5</p>
        <form onSubmit={handleSubmit}>
          <div className="profile-form-grid md:grid-cols-1">
            <SelectAutoload
              id="profile-creation-company-industrySectorTitle"
              apiAutoloadRoute="/api/employers/industry-sectors"
              disabled={!employerInfo?.is_verified_employee}
              label="Industry Sector *"
              className="select-autoload"
              value={industry}
              onChange={(val) => {
                setIndustry(val);
                setCompanyData({
                  ...companyData,
                  industrySectorId: val?.industry_sector_id!,
                  industrySectorTitle: val?.sector_title,
                });
              }}
              placeholder="Your company's industry sector"
              loadingText="Retrieving industry sectors..."
              getOptionLabel={(option: IndustrySectorDropdownDTO) =>
                option.sector_title
              }
              getOptionId={(option: IndustrySectorDropdownDTO) =>
                option.industry_sector_id ?? ""
              }
              getOptionFromId={(
                options: IndustrySectorDropdownDTO[],
                id: string,
              ) =>
                options.find((item) => item.industry_sector_id === id) || null
              }
              required
            />
          </div>

          <fieldset>
            <legend>
              <h2>
                Logo <span className="subtitle-optional">(optional)</span>
              </h2>
            </legend>
            <AvatarUpload
              id="profile-creation-company-logoUrl"
              fileTypeText="File types: SVG, PNG, JPG, GIF, or WEBP"
              accept=".svg,.png,.jpg,.jpeg,.gif,.webp"
              maxSizeMB={5}
              userId={companyData.companyId!}
              onImageUpload={handleImageUpload}
              initialImageUrl={companyData.logoUrl || ""}
              disabled={!employerInfo?.is_verified_employee}
              apiPath="/api/companies/avatar/upload"
            />
          </fieldset>

          <fieldset>
            <h2>Basic Info</h2>
            <div className="profile-form-grid tablet:grid-cols-2">
              <InputTextWithLabel
                id="profile-creation-company-websiteUrl"
                placeholder="www.company.com"
                onChange={handleFieldChange}
                value={companyData.websiteUrl ?? ""}
                disabled={!employerInfo?.is_verified_employee}
                required
              >
                Company Website
              </InputTextWithLabel>

              <InputTextWithLabel
                type="email"
                id="profile-creation-company-companyEmail"
                placeholder="hello@company.com"
                onChange={handleFieldChange}
                value={companyData.companyEmail ?? ""}
                disabled={!employerInfo?.is_verified_employee}
                required
              >
                Company Email
              </InputTextWithLabel>

              <InputTextWithLabel
                type="tel"
                id="profile-creation-company-companyPhone"
                onChange={handleFieldChange}
                placeholder="(555) 123-4567"
                value={companyData.companyPhone ?? ""}
                disabled={!employerInfo?.is_verified_employee}
                required
              >
                Company Phone Number
              </InputTextWithLabel>

              <DatePicker
                label={"Year Founded *"}
                views={["year"]}
                value={yearFounded}
                onChange={(newValue) => {
                  setYearFounded(newValue);
                  setCompanyData({
                    ...companyData,
                    yearFounded: newValue?.year().toString() || "",
                  });
                }}
                disabled={!employerInfo?.is_verified_employee}
              />

              <SelectOptionsWithLabel
                id="profile-creation-company-companySize"
                onChange={handleFieldChange}
                options={[
                  { label: "1-10", value: "1-10" },
                  { label: "11-50", value: "11-50" },
                  { label: "51-200", value: "51-200" },
                  { label: "201-500", value: "201-500" },
                  { label: "501-1000", value: "501-1000" },
                  { label: "1001-5000", value: "1001-5000" },
                  { label: "5000+", value: "5000+" },
                ]}
                placeholder="Please select"
                value={companyData.companySize ?? ""}
                disabled={!employerInfo?.is_verified_employee}
                required
              >
                Company Size
              </SelectOptionsWithLabel>

              <InputTextWithLabel
                id="profile-creation-company-estimatedAnnualHires"
                name="profile-creation-company-estimatedAnnualHires"
                placeholder="100"
                onChange={handleFieldChange}
                value={companyData.estimatedAnnualHires || ""}
                disabled={!employerInfo?.is_verified_employee}
                required
              >
                Estimated Annual Hires
              </InputTextWithLabel>

              <TextFieldWithAutocomplete
                apiSearchRoute="/api/postal-geo-data/zip/search/"
                fieldLabel="Company Location *"
                id="profile-creation-company-companyAddresses"
                className="text-field-autocomplete"
                searchingText="Searching..."
                noResultsText="No postal code found..."
                value={selectedWorkLocation?.zip ?? ""}
                disabled={!employerInfo?.is_verified_employee}
                onChange={handleAddressSelection}
                searchPlaceholder="Company Location Postal Code"
                getOptionLabel={(option: ReadAddressDTO) =>
                  `${option?.city}, ${option?.stateCode} ${option?.zip}`
                }
              />

              <div className="selected-locations">
                {companyData?.companyAddresses?.map((location, index) => (
                  <div key={index} className="location-tag">
                    {location?.city}, {location?.stateCode} {location?.zip}
                  </div>
                ))}
              </div>
            </div>
          </fieldset>

          <div className="profile-form-progress-btn-group">
            <PillButton
              className="custom-outline-btn"
              onClick={() => router.push("/edit-profile/employer/profile")}
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
