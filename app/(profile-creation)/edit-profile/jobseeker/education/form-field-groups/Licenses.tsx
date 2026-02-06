import React, { memo, useCallback } from "react";
import PillButton from "@/app/ui/components/PillButton";
import InputTextWithLabel from "@/app/ui/components/InputTextWithLabel";
import { v4 as uuidv4 } from "uuid";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Dayjs } from "dayjs";
import { Close } from "@mui/icons-material";

const classNamePrefix = "profile-creation-license-group-";
const classForName = "name";
const classIssuingOrg = "issuingOrg";
const classCredentialId = "credentialId";
const classCredentialUrl = "credentialUrl";
const classIssueDate = "issueDate";
const classExpirationDate = "expiryDate";

export interface LicenseData {
  certId: string;
  [classForName]: string;
  [classIssuingOrg]: string;
  [classCredentialId]: string;
  [classCredentialUrl]: string;
  [classIssueDate]: Dayjs | null; // fixme: why does this have to have the option of null. This allows null entries in certificates table and it doesn't make sense to allow null values.
  [classExpirationDate]: Dayjs | null; // fixme: why do this have to have the option of null?
}

export function defaultLicenseData() {
  return {
    certId: uuidv4(),
    [classForName]: "",
    [classIssuingOrg]: "",
    [classCredentialId]: "",
    [classCredentialUrl]: "",
    [classIssueDate]: null,
    [classExpirationDate]: null,
  };
}

interface Props {
  data: LicenseData[];
  onRemove: (uid: string) => void;
  onUpdate: (key: string, value: any) => void;
}

export default memo(function Licenses({ data, onRemove, onUpdate }: Props) {
  const handleChange = useCallback(
    <K extends keyof LicenseData>(index: number, key: K, value: any) => {
      const changedLicenses: LicenseData[] = [...data];
      const updatedLicense = changedLicenses[index];
      updatedLicense[key] = value;
      onUpdate("licenses", changedLicenses);
    },
    [data, onUpdate],
  );

  return data.map((license, index) => (
    <fieldset key={classNamePrefix + license.certId + "-key"}>
      <legend className="flex w-full justify-between">
        <h3>License or Certification {index + 1}</h3>
        <PillButton onClick={() => onRemove(license.certId)} variant="outlined">
          <Close className="h-5 w-5" />
        </PillButton>
      </legend>
      <div className="profile-form-grid">
        <InputTextWithLabel
          id={classNamePrefix + license.certId + "-" + classForName}
          className="w-full"
          placeholder="Example: Microsoft certified network associate security"
          onChange={(e) => handleChange(index, classForName, e.target.value)}
          required
          value={license[classForName]}
        >
          Name: *
        </InputTextWithLabel>
        <InputTextWithLabel
          id={classNamePrefix + license.certId + "-" + classIssuingOrg}
          className="w-full"
          placeholder="Example: Microsoft"
          onChange={(e) => handleChange(index, classIssuingOrg, e.target.value)}
          required
          value={license[classIssuingOrg]}
        >
          Issuing organization: *
        </InputTextWithLabel>
      </div>
      <div className="profile-form-grid md:grid-cols-2">
        <InputTextWithLabel
          id={classNamePrefix + license.certId + "-" + classCredentialId}
          onChange={(e) =>
            handleChange(index, classCredentialId, e.target.value)
          }
          value={license[classCredentialId]}
        >
          Credential ID:
        </InputTextWithLabel>
        <InputTextWithLabel
          id={classNamePrefix + license.certId + "-" + classCredentialUrl}
          onChange={(e) =>
            handleChange(index, classCredentialUrl, e.target.value)
          }
          value={license[classCredentialUrl]}
        >
          Credential URL:
        </InputTextWithLabel>
        <DatePicker
          label={"Issue date"}
          views={["month", "year"]}
          value={license[classIssueDate] || null}
          onChange={(val) =>
            handleChange(
              index,
              classIssueDate,
              val && val.isValid() ? val : null,
            )
          }
          slotProps={{ textField: { fullWidth: true } }}
        />
        <DatePicker
          label={"Expiration date"}
          views={["month", "year"]}
          value={license[classExpirationDate] || null}
          onChange={(val) =>
            handleChange(
              index,
              classExpirationDate,
              val && val.isValid() ? val : null,
            )
          }
          slotProps={{ textField: { fullWidth: true } }}
        />
      </div>
    </fieldset>
  ));
});
