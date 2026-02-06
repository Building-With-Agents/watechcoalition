export type PostEmployerPersonalDTO = {
  userId: string;
  firstName: string;
  lastName: string;
  birthDate: string;
  email: string;
  phoneCountryCode?: string | null;
  phone?: string | null;
  photoUrl?: string | null;
};

export type ReadEmployerPersonalDTO = {
  employerId?: string | null;
  userId?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  birthDate?: string | null;
  email?: string | null;
  phoneCountryCode?: string | null;
  phone?: string | null;
  photoUrl?: string | null;
};

export type PostEmployerWorkDTO = {
  userId: string;
  currentJobTitle: string;
  linkedInUrl: string;
  workAddressId?: string;
  // hasAgreedTerms: boolean;
};

export type ReadEmployerWorkDTO = {
  userId?: string | null;
  employerId?: string | null;
  currentJobTitle?: string | null;
  linkedInUrl?: string | null;
  workAddressId?: string | null;
  isVerifiedEmployee?: boolean | null;
};

export type CompanyInfoSummaryDTO = {
  companyId?: string;
  companyName?: string;
  companyLogoUrl?: string;
  isVerifiedCompany?: boolean;
  companyAddress?: ReadAddressDTO;
};

export type ReadAddressDTO = {
  addressId: string;
  city: string;
  state: string;
  stateCode: string;
  zip: string;
  county: string;
  lat?: string;
  lon?: string;
} | null;

export type PostAddressDTO = {
  addressId?: string;
  city?: string;
  state?: string;
  stateCode?: string;
  zip: string;
  county?: string;
  lat?: string;
  lon?: string;
};

export type PostCompanyInfoDTO = {
  userId: string;
  employerId?: string;
  companyId?: string;
  industrySectorId?: string | null;
  industrySectorTitle?: string | null;
  companyName: string;
  companyAddresses?: PostAddressDTO[] | null;
  logoUrl?: string | null;
  aboutUs?: string | null;
  companyEmail: string;
  yearFounded: string;
  websiteUrl?: string | null;
  videoUrl?: string | null;
  phoneCountryCode?: string | null;
  companyPhone?: string | null;
  mission?: string | null;
  vision?: string | null;
  companySize: string;
  estimatedAnnualHires: string;
};

export type ReadCompanyInfoDTO = {
  companyId: string;
  industrySectorId?: string | null;
  industrySectorTitle?: string | null;
  companyName: string;
  companyAddresses?: ReadAddressDTO[];
  logoUrl?: string | null;
  aboutUs?: string | null;
  companyEmail: string | null;
  yearFounded?: string | null;
  websiteUrl?: string | null;
  videoUrl?: string | null;
  phoneCountryCode?: string | null;
  companyPhone?: string | null;
  mission?: string | null;
  vision?: string | null;
  companySize?: string | null;
  estimatedAnnualHires?: string | null;
  isApproved?: boolean | null;
  createdBy?: string | null;
};

export type PostEmployerAboutDTO = {
  companyId: string;
  aboutUs: string;
};

export type ReadEmployerAboutDTO = {
  companyId?: string;
  aboutUs?: string | null;
};

export type PostEmployerMissionDTO = {
  // companyId: string;
  mission: string;
};

export type ReadEmployerMissionDTO = {
  companyId?: string;
  mission?: string | null;
};

export type PostEmployerVideoDTO = {
  companyId: string;
  videoUrl: string;
};

export type ReadEmployerVideoDTO = {
  companyId?: string;
  videoUrl?: string | null;
};

export type PostCompanyTestimonialsDTO = {
  companyId: string;
  employerId: string;
  text: string;
  author: string;
};

export type ReadCompanyTestimonialsDTO = {
  testimonyId: string;
  companyId?: string;
  employerId?: string | null;
  text?: string;
  author?: string;
};

export type PostCompanySocialLinkDTO = {
  companyId: string;
  socialPlatformId: string;
  employerId: string;
  socialUrl: string;
};

export type ReadCompanySocialLinkDTO = {
  companySocialId?: string;
  socialPlatformId?: string;
  companyId?: string;
  employerId?: string | null;
  socialUrl?: string;
  platform?: string;
  platformIconUrl?: string;
};

export type PostEmployerProfileDTO = {
  // Personal Info
  userId: string;
  firstName: string;
  lastName: string;
  birthDate?: string;
  email: string;
  phone?: string | null;
  photoUrl?: string | null;
  isApprovedEmployee?: boolean;

  // Work Info
  currentJobTitle: string;
  linkedInUrl?: string;
  workAddressId?: string;
  hasAgreedTerms: boolean;

  // Company Info
  employerId?: string;
  companyId?: string;
  industrySectorId?: string | null;
  industrySectorTitle?: string | null;
  companyName: string;
  companyAddresses?: PostAddressDTO[] | null;
  logoUrl?: string | null;
  aboutUs?: string | null;
  companyEmail: string;
  yearFounded?: string | null;
  websiteUrl?: string | null;
  videoUrl?: string | null;
  phoneCountryCode?: string | null;
  companyPhone?: string | null;
  mission?: string | null;
  vision?: string | null;
  companySize: string;
  estimatedAnnualHires: string;

  // About Us
  aboutUsDetails: string;

  // Mission Statement
  missionStatement: string;

  // Video Info
  companyVideoUrl: string;
};

export type ReadEmployerProfileDTO = {
  // Personal Info
  employerId?: string | null;
  userId?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  birthDate?: string | null;
  email?: string | null;
  phone?: string | null;
  photoUrl?: string | null;

  // Work Info
  currentJobTitle?: string | null;
  linkedInUrl?: string | null;
  workAddressId?: string | null;
  isVerifiedEmployee?: boolean | null;

  // Company Info
  companyId?: string | null;
  industrySectorId?: string | null;
  industrySectorTitle?: string | null;
  companyName?: string | null;
  companyAddresses?: ReadAddressDTO[] | null;
  logoUrl?: string | null;
  aboutUs?: string | null;
  companyEmail?: string | null;
  yearFounded?: string | null;
  websiteUrl?: string | null;
  videoUrl?: string | null;
  phoneCountryCode?: string | null;
  companyPhone?: string | null;
  mission?: string | null;
  vision?: string | null;
  companySize?: string | null;
  estimatedAnnualHires?: string | null;
  isApproved?: boolean | null;
  createdBy?: string | null;

  // About Us
  aboutUsDetails?: string | null;

  // Mission Statement
  missionStatement?: string | null;

  // Video Info
  companyVideoUrl?: string | null;
};
