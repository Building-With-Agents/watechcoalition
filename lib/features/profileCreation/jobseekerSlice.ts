"use client";
import { createSlice, type PayloadAction } from "@reduxjs/toolkit";
import {
  HighestCompletedEducationLevel,
  JsDisclosuresPostDTO,
  JsEducationPageDTO,
  JsIntroPostDTO,
  JsPreferencesDTO,
  JsShowcaseDTO,
  JsWorkExpDTO,
  JsWorkDTO,
  JsCareerPrepPathwaySkillsDTO,
  JsCareerPrepDurableSkillsDTO,
  JsCareerPrepProfessionalBrandingDTO,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import {
  AgreementLevel,
  SkillLevel,
  TimeUntilCompletion,
} from "@/app/lib/admin/careerPrep";

interface JsEducationPageBlankHighestLevelDTO
  extends Omit<JsEducationPageDTO, "highestLevelOfStudy"> {
  highestLevelOfStudy: HighestCompletedEducationLevel | "";
}

interface JsWorkExpStringDateDTO extends Omit<JsWorkExpDTO, "workExperiences"> {
  workExperiences?: JsWorkStringDateDTO[];
}

interface JsWorkStringDateDTO extends Omit<JsWorkDTO, "startDate" | "endDate"> {
  startDate: string;
  endDate: string | null;
}

interface JsShowcaseWithResumeDTO extends JsShowcaseDTO {
  resumeUrl: string | null;
}

// Define a type for the slice state
export interface JobseekerState {
  introduction: JsIntroPostDTO;
  education: JsEducationPageBlankHighestLevelDTO;
  workExperience: JsWorkExpStringDateDTO;
  showcase: JsShowcaseWithResumeDTO;
  preferences: JsPreferencesDTO;
  pathwaySkills: JsCareerPrepPathwaySkillsDTO;
  durableSkills: JsCareerPrepDurableSkillsDTO;
  professionalBranding: JsCareerPrepProfessionalBrandingDTO;
  disclosures: JsDisclosuresPostDTO;
}

// Define the initial state using that type
export const initialState: JobseekerState = {
  introduction: {
    userId: "",
    photoUrl: null,
    firstName: "",
    lastName: "",
    CareerPrepAssessment: {
      streetAddress: undefined,
      pronouns: "",
    },
    birthDate: null,
    phoneCountryCode: null,
    phone: null,
    zipCode: "",
    state: null,
    city: null,
    county: null,
    email: "",
    introHeadline: null,
    currentJobTitle: null,
  },
  education: {
    userId: "",
    jobseekerId: "",
    highestLevelOfStudy: "",
    CareerPrepAssessment: {
      expectedEduCompletion: TimeUntilCompletion.NA,
    },
    educations: [],
    certifications: [],
    projects: [],
  },
  workExperience: {
    userId: "",
    yearsWorkExperience: "",
    CareerPrepAssessment: {
      experienceWithInterview: false,
      experienceWithApplying: false,
    },
    monthsInternshipExperience: null,
    isAuthorizedToWorkUsa: undefined,
    requiresSponsorship: undefined,
    workExperiences: [],
  },
  showcase: {
    userId: "",
    skills: [],
    introduction: null,
    portfolioUrl: null,
    portfolioPassword: null,
    video_url: null,
    resumeUrl: null,
  },
  preferences: {
    userId: "",
    targetedPathwayId: null,
    targetedPathway: null,
    preferredEmploymentType: null,
  },
  pathwaySkills: {
    userId: "",
    targetedPathway: null,
    CareerPrepAssessment: {
      cybersecurity: null,
      dataAnalytics: null,
      itAndCloudComputing: null,
      softwareDevelopment: null,
    },
  },
  durableSkills: {
    userId: "",
    CareerPrepAssessment: {
      durableSkills: {
        overallAverage: null,
        emotionManagement: SkillLevel.Fair,
        empathy: SkillLevel.Fair,
        goalSetting: SkillLevel.Fair,
        timeManagement: SkillLevel.Fair,
        adaptability: SkillLevel.Fair,
        criticalThinking: SkillLevel.Fair,
        creativity: SkillLevel.Fair,
        resilience: SkillLevel.Fair,
        communication: SkillLevel.Fair,
        activeListening: SkillLevel.Fair,
        conflictResolution: SkillLevel.Fair,
        nonverbalCommunication: SkillLevel.Fair,
        teamwork: SkillLevel.Fair,
        trustBuilding: SkillLevel.Fair,
        leadership: SkillLevel.Fair,
        perspectiveTaking: SkillLevel.Fair,
        culturalAwareness: SkillLevel.Fair,
        relationshipBuilding: SkillLevel.Fair,
        documentationSkills: SkillLevel.Fair,
      },
    },
  },
  professionalBranding: {
    userId: "",
    CareerPrepAssessment: {
      professionalBrandingAndJobMarketReadiness: {
        overallAverage: null,
        personalBrand: AgreementLevel.Neutral,
        onlinePresence: AgreementLevel.Neutral,
        elevatorPitch: AgreementLevel.Neutral,
        resumeEffectiveness: AgreementLevel.Neutral,
        coverLetterEffectiveness: AgreementLevel.Neutral,
        interviewExperience: AgreementLevel.Neutral,
        responseTechnique: AgreementLevel.Neutral,
        followUpImportance: AgreementLevel.Neutral,
        onlineNetworking: AgreementLevel.Neutral,
        eventNetworking: AgreementLevel.Neutral,
        relationshipManagement: AgreementLevel.Neutral,
        jobSearchStrategy: AgreementLevel.Neutral,
        materialDistribution: AgreementLevel.Neutral,
        networkingTechniques: AgreementLevel.Neutral,
        onboardingBestPractices: AgreementLevel.Neutral,
        developmentPlan: AgreementLevel.Neutral,
        mentorship: AgreementLevel.Neutral,
      },
    },
  },
  disclosures: {
    userId: "",
    isVeteran: "",
    disabilityStatus: "",
    disability: "",
    gender: "",
    race: "",
    ethnicity: "",
    CareerPrepAssessment: {
      priorityPopulations: undefined,
    },
  },
};

// Actions
export const jobseekerSlice = createSlice({
  name: "jobseeker",
  // `createSlice` will infer the state type from the `initialState` argument
  initialState,

  // REVIEW: each field will need its own reducer? unsure if best, seems there should be a way to deconstruct ...state then update this.id/param specific?
  reducers: {
    setIntroduction: (state, action: PayloadAction<JsIntroPostDTO>) => {
      state.introduction = action.payload;
    },
    setEducation: (
      state,
      action: PayloadAction<JsEducationPageBlankHighestLevelDTO>,
    ) => {
      state.education = action.payload;
    },
    setWorkExperience: (
      state,
      action: PayloadAction<JsWorkExpStringDateDTO>,
    ) => {
      state.workExperience = action.payload;
    },
    setShowcase: (state, action: PayloadAction<JsShowcaseWithResumeDTO>) => {
      state.showcase = action.payload;
    },
    setPreferences: (state, action: PayloadAction<JsPreferencesDTO>) => {
      state.preferences = action.payload;
    },
    setDisclosures: (state, action: PayloadAction<JsDisclosuresPostDTO>) => {
      state.disclosures = action.payload;
    },
    setPathwaySkills: (
      state,
      action: PayloadAction<JsCareerPrepPathwaySkillsDTO>,
    ) => {
      state.pathwaySkills = action.payload;
    },
    setDurableSkills: (
      state,
      action: PayloadAction<JsCareerPrepDurableSkillsDTO>,
    ) => {
      state.durableSkills = action.payload;
    },
    setProfessionalBranding: (
      state,
      action: PayloadAction<JsCareerPrepProfessionalBrandingDTO>,
    ) => {
      state.professionalBranding = action.payload;
    },
  },
});

export const {
  setIntroduction,
  setEducation,
  setWorkExperience,
  setShowcase,
  setPreferences,
  setDisclosures,
  setPathwaySkills,
  setDurableSkills,
  setProfessionalBranding,
} = jobseekerSlice.actions;

// TODO: Review if needed in future
// Other code such as selectors can use the imported `RootState` type
// export const selectCount = (state: RootState) => state.counter.value;

export default jobseekerSlice.reducer;
