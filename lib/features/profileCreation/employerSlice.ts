"use client";
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import {
  PostEmployerProfileDTO,
  PostEmployerPersonalDTO,
  PostCompanyInfoDTO,
  PostEmployerAboutDTO,
  PostEmployerVideoDTO,
  PostEmployerMissionDTO,
  PostEmployerWorkDTO,
} from "@/data/dtos/EmployerProfileCreationDTOs";

// Define a type for the slice state
export interface EmployerState {
  profile: PostEmployerProfileDTO;
  personal: PostEmployerPersonalDTO;
  company: PostCompanyInfoDTO;
  about: PostEmployerAboutDTO;
  mission: PostEmployerMissionDTO;
  video: PostEmployerVideoDTO;
  disclosures: PostEmployerWorkDTO;
}

// Define the initial state using that type
export const initialState: EmployerState = {
  profile: {
    // Personal Info
    userId: "",
    firstName: "",
    lastName: "",
    birthDate: "",
    email: "",
    phone: null,
    photoUrl: null,

    // Work Info
    currentJobTitle: "",
    linkedInUrl: "",
    workAddressId: "",
    hasAgreedTerms: false,

    // Company Info
    companyId: "",
    industrySectorId: null,
    industrySectorTitle: null,
    companyName: "",
    companyAddresses: null,
    logoUrl: null,
    aboutUs: "",
    companyEmail: "",
    yearFounded: "",
    websiteUrl: null,
    videoUrl: null,
    phoneCountryCode: null,
    companyPhone: null,
    mission: null,
    vision: null,
    companySize: "",
    estimatedAnnualHires: "",

    // Additional Details
    aboutUsDetails: "",
    missionStatement: "",
    companyVideoUrl: "",
  },

  personal: {
    userId: "",
    firstName: "",
    lastName: "",
    birthDate: "",
    email: "",
    phoneCountryCode: null,
    phone: null,
    photoUrl: null,
  },
  company: {
    userId: "",
    employerId: "",
    companyId: "",
    industrySectorId: null,
    industrySectorTitle: null,
    companyName: "",
    companyAddresses: null,
    logoUrl: null,
    aboutUs: null, //ABOUT
    companyEmail: "",
    yearFounded: "",
    websiteUrl: null,
    videoUrl: null, //VIDEO
    phoneCountryCode: null,
    companyPhone: null,
    mission: null, //MISSION
    vision: null,
    companySize: "",
    estimatedAnnualHires: "",
  },
  about: {
    companyId: "",
    aboutUs: "",
  },
  mission: {
    // companyId: '',
    mission: "",
  },
  disclosures: {
    userId: "",
    currentJobTitle: "",
    linkedInUrl: "",
    workAddressId: "",
  },
  video: {
    companyId: "",
    videoUrl: "",
  },
};

// Actions
export const employerSlice = createSlice({
  name: "employer",
  // `createSlice` will infer the state type from the `initialState` argument
  initialState,

  // REVIEW: each field will need its own reducer? unsure if best, seems there should be a way to deconstruct ...state then update this.id/param specific?
  reducers: {
    setProfile: (state, action: PayloadAction<PostEmployerProfileDTO>) => {
      state.profile = action.payload;
    },
    // Update specific fields of the profile
    updateProfileField: <K extends keyof PostEmployerProfileDTO>(
      state: EmployerState,
      action: PayloadAction<{ field: K; value: PostEmployerProfileDTO[K] }>,
    ) => {
      const { field, value } = action.payload;
      state.profile[field] = value;
    },
    setAbout: (state, action: PayloadAction<PostEmployerAboutDTO>) => {
      state.about = action.payload;
    },
    setMission: (state, action: PayloadAction<PostEmployerMissionDTO>) => {
      state.mission = action.payload;
    },
    setVideo: (state, action: PayloadAction<PostEmployerVideoDTO>) => {
      state.video = action.payload;
    },
    setDisclosures: (state, action: PayloadAction<PostEmployerWorkDTO>) => {
      state.disclosures = action.payload;
    },
    setPersonal: (state, action: PayloadAction<PostEmployerPersonalDTO>) => {
      state.personal = action.payload;
    },
    setCompany: (state, action: PayloadAction<PostCompanyInfoDTO>) => {
      state.company = action.payload;
    },
  },
});

export const {
  setProfile,
  updateProfileField,
  setAbout,
  setMission,
  setVideo,
  setDisclosures,
  setPersonal,
  setCompany,
} = employerSlice.actions;

export default employerSlice.reducer;
