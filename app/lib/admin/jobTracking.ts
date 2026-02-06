// Job Placement / Employment Tracking
export enum EmploymentStatus {
  EmployedInFieldPartner = "Employed In-field by an employer who partners with your training program",
  EmployedInFieldNonPartner = "Employed In-field by an employer who does not partner with your training program",
  SeekingEmploymentInField = "Still seeking employment in-field",
  NotSeekingEmploymentInField = "Not seeking employment in-field",
  CouldNotContact = "Could not contact",
}

export enum EmploymentType {
  FullTime = "Full-time",
  PartTime = "Part-time",
  Contract = "Contract",
  Seasonal = "Seasonal",
  EarnAndLearn = "Earn and Learn",
  Other = "Other",
}

export enum EarnLearnType {
  RegisteredApprenticeship = "Registered Apprenticeship",
  NonRegisteredApprenticeship = "Non-registered Apprenticeship",
  Internship = "Internship",
  CustomizedTraining = "Customized Training",
  IncumbentWorkerTraining = "Incumbent Worker Training",
  Other = "Other (Transitional Jobs, Cooperatives, Practicums, Residences, or Fellowships)",
}

// Tracked NAICS codes for reporting
export enum OccupationCode {
  ComputerSystemsAnalysts = "Computer Systems Analysts (15-1211)",
  InformationSecurityAnalysts = "Information Security Analysts (15-1212)",
  ComputerInformationResearchScientists = "Computer and Information Research Scientists (15-1221)",
  ComputerNetworkSupportSpecialists = "Computer Network Support Specialists (15-1231)",
  ComputerUserSupportSpecialists = "Computer User Support Specialists (15-1232)",
  ComputerNetworkArchitects = "Computer Network Architects (15-1241)",
  DatabaseAdministrators = "Database Administrators (15-1242)",
  DatabaseArchitects = "Database Architects (15-1243)",
  NetworkComputerSystemsAdministrators = "Network and Computer Systems Administrators (15-1244)",
  ComputerProgrammers = "Computer Programmers (15-1251)",
  SoftwareDevelopers = "Software Developers (15-1252)",
  SoftwareQualityAssuranceAnalystsTesters = "Software Quality Assurance Analysts and Testers (15-1253)",
  WebDevelopers = "Web Developers (15-1254)",
  WebDigitalInterfaceDesigners = "Web and Digital Interface Designers (15-1255)",
  OperationsResearchAnalysts = "Operations Research Analysts (15-2031)",
  DataScientists = "Data Scientists (15-2051)",
  ComputerHardwareEngineers = "Computer Hardware Engineers (17-2061)",
  ElectronicsEngineers = "Electronics Engineers (17-2072)",
  ElectronicsRepairers = "Electronics Repairers (49-2094)",
  HVACMechanics = "HVAC Mechanics (49-9021)",
  OtherComputerOccupations = "OTHER Computer Occupations (15-1299)",
}
