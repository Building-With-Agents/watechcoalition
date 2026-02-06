"use client";
import { Box } from "@mui/material";
import { DataGrid, GridColDef, GridToolbar } from "@mui/x-data-grid";
import Link from "next/link";
import ViewResume from "./ViewResume";
import SelfAssignCaseButton from "./SelfAsignCaseButton";
import OpenInNewIcon from "@mui/icons-material/OpenInNew";
import { CareerPrepStatus } from "@/app/lib/admin/careerPrep";
import { PoolCategories } from "@/app/lib/poolAssignment";
import EnrollmentStatusDropDown from "./EnrollmentStatusDropDown";
import {
  BrandingRating,
  CybersecurityRating,
  DataAnalyticsRating,
  DurableSkillsRating,
  ITCloudRating,
  SoftwareDevRating,
} from "@prisma/client";
import { AssessmentModal } from "./SelfAssementReadOnly";
import ScreenedDropdown from "./ScreenedDropdown";
export interface CareerPrepGridData {
  jobseeker_id: string;
  first_name: string;
  last_name: string;
  email: string;
  careerPrepTrackRecommendation: string;
  "CP Enrollment Status": CareerPrepStatus;
  HighestEdLevel: string;
  "Pool Type": PoolCategories;
  //"Pathway Title": string;
  // JobseekerCreatedAt: Date;
  // JobseekerUpdatedAt: Date;
  user_id: string;
  CybersecurityRating: CybersecurityRating[];
  DataAnalyticsRating: DataAnalyticsRating[];
  ITCloudRating: ITCloudRating[];
  SoftwareDevRating: SoftwareDevRating[];
  DurableSkillsRating: DurableSkillsRating[];
  BrandingRating: BrandingRating[];
  AppearOnShowCase: boolean;
}
const ratingFields = [
  { key: "CybersecurityRating", label: "Cybersecurity" },
  { key: "DataAnalyticsRating", label: "Data Analytics" },
  { key: "ITCloudRating", label: "IT & Cloud" },
  { key: "SoftwareDevRating", label: "Software Development" },
  { key: "DurableSkillsRating", label: "Durable Skills" },
  { key: "BrandingRating", label: "Branding" },
];

const ratingColumns: GridColDef[] = ratingFields.map(({ key, label }) => ({
  field: key,
  headerName: label,
  renderCell: (params) => (
    <AssessmentModal list={params.row[key]} title={label} />
  ),
}));

export default function CareerPrepDataGrid({
  clients,
  ShowClaimButton,
}: {
  clients: CareerPrepGridData[];
  ShowClaimButton: boolean;
}) {
  const columns: GridColDef[] = [
    {
      field: "careerPrepAssessmentDate",
      headerName: "Application Date",
    },
    { field: "first_name", headerName: "First Name" },
    { field: "last_name", headerName: "Last Name" },
    { field: "email", headerName: "email", width: 200 },
    {
      field: "actions",
      sortable: false,
      width: 130,
      headerName: "Profile",
      renderCell: (params) => (
        <Link
          href={"/services/jobseekers/" + params.id}
          target="_blank"
          className="LINK"
        >
          View Profile <OpenInNewIcon />
        </Link>
      ),
    },
    {
      field: "resume",
      sortable: false,
      headerName: "Resume",
      renderCell: (params) => <ViewResume userId={params.row.user_id} />,
    },
    {
      field: "AppearOnShowCase",
      width: 130,
      align: "center",
      headerName: "AppearOnShowCase",
      renderCell: (params) => (
        <ScreenedDropdown
          screened={params.row.AppearOnShowCase}
          jobseekerId={params.row.jobseeker_id}
        />
      ),
    },
    // { field: "careerPrepTrackRecommendation", headerName: "track" },
    {
      field: "Status",
      headerName: "CP Enrollment Status",
      renderCell: (params) =>
        params.row["CP Enrollment Status"] ? (
          <EnrollmentStatusDropDown
            careerPrepEnrollmentStatus={params.row["CP Enrollment Status"]}
            jobseekerId={params.row.jobseeker_id}
          />
        ) : (
          "Not Enrolled"
        ),
      width: 160,
    },
    ...ratingColumns,
    // { field: "HighestEdLevel", headerName: "HighestEdLevel", width: 160 },
    //{ field: "Pool Type", headerName: "Pool Type" },
    // { field: "Pathway Title", headerName: "Pathway Title" },
    // { field: "JobseekerCreatedAt", headerName: "JobseekerCreatedAt" },
    // { field: "JobseekerUpdatedAt", headerName: "JobseekerUpdatedAt" },

    // { field: "EnrollmentDate", headerName: "EnrollmentDate" },
  ];
  if (ShowClaimButton) {
    columns.unshift({
      field: "jobseeker_id",
      sortable: false,
      width: 75,
      headerName: "Claim",
      renderCell: (params) => (
        <SelfAssignCaseButton jobseekerId={params.row.jobseeker_id} />
      ),
    });
  }
  return (
    <Box>
      <DataGrid
        rows={clients}
        getRowId={(row: CareerPrepGridData) => row.jobseeker_id}
        columns={columns}
        slots={{ toolbar: GridToolbar }}
        slotProps={{
          toolbar: {
            showQuickFilter: true,
          },
        }}
        initialState={{
          sorting: {
            sortModel: [{ field: "EnrollmentDate", sort: "desc" }], // Default sort
          },
        }}
      />
    </Box>
  );
}
