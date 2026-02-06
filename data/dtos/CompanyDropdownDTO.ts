export type CompanyDropdownDTO = {
  companyId: string;
  companyName: string;
  logoUrl?: string;
  industrySectorId?: string;
  websiteUrl: string | null;
  companyEmail: string;
  companyPhone: string | null;
  yearFounded: number | null;
  companySize: string;
  estimatedAnnualHires: string;
  approvedCompany: boolean;
  createdBy: string; //employerId uuidv4
};
