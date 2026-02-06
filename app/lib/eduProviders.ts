import { PrismaClient } from "@prisma/client";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { EducationLevel } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { v4 as uuidv4 } from "uuid";
import { devLog } from "@/app/lib/utils";

const prisma: PrismaClient = getPrismaClient();

export type ReadEduProviderDTO = {
  eduProviderId: string; //edu_providers.id
  eduLevel?: EducationLevel; // edu_providers.edu_type
  providerName: string; // edu_providers.name
  logoUrl: string;
  contactName?: string; // edu_providers.contact
  contactEmail?: string; // edu_providers.contact_email
  url?: string; // edu_providers.edu_url
  mission?: string; // edu_providers.mission
  providerDescription?: string; // edu_providers.providerDescription
  setsApartStatement?: string; // edu_providers.setsApartStatement
  screeningCriteria?: string; // edu_providers.screeningCriteria
  recruitingSources?: string; // edu_providers.recruitingSources
  programCount?: string; // edu_providers.programCount
  cost?: string; // edu_providers.cost
  isAdminReviewed?: boolean; // edu_providers.isAdminReviewed
  isCoalitionMember?: boolean; // edu_providers.isCoalitionMember
  createdBy?: string; // edu_providers.userId
};

export type ReadEduProviderProgramCardDTO = {
  programId: string; // provider_programs.training_program_id
  logoUrl: string; // will use blobStorage ss method to retrieve image url. getEduProviderLogo(eduProviderId)
  programName: string; // provider_programs join programs on program_id
  eduProviderId: string; //edu_providers.id
  eduProviderName: string; // provider_programs join edu_providers on edu_provider_id
  eduLevel: EducationLevel | null; // provider_programs.eduLevel
  programLength: string; // provider_programs.programLength
  tuition?: string; // provider_programs.tuition
  fees?: string; // provider_programs.fees
  locationType: LocationType | null; // provider_programs.locationType (enum LocationType)
  pathway: EduProviderPathways[];
};

export type ReadEduProviderProgramDetailDTO = {
  programId: string; // provider_programs.training_program_id
  logoUrl: string; // will use blobStorage ss method to retrieve image url. getEduProviderLogo(eduProviderId)
  programName: string; // provider_programs join programs on program_id
  eduProviderId: string; //edu_providers.id
  eduProviderName: string; // provider_programs join edu_providers on edu_provider_id
  description?: string;
  targetedJobRoles?: string[];
  locations: string[]; // provider_programs.locations. Saved as TEXT field in db but separate into list on DTO delimiter (~)
  programLength: string; // provider_programs.programLength
  about: string; // provider_programs.about Possibly use Quill to implement this
  tuition?: string; // provider_programs.tuition
  fees?: string; // provider_programs.fees
  costSummary?: string; // provider_programs.costSummary
  locationType: LocationType | null; // provider_programs.locationType (enum LocationType)
  getStartedUrl: string; // provider_programs.getStartedUrl
  faq: { question: string; answer: string }[]; // provider_programs.faq as TEXT field parse response with JSON.parse, JSON.stringify
  pathways: EduProviderPathways[]; // provider_programs.pathways will need converted from string to list and each item cast into EduProviderPathways enum
};

export type PostEduProviderProgramDetailDTO = {
  programName: string; // provider_programs join programs on program_id (if doesn't exist in programs table add it first)
  logoUrl?: string; // will use blobStorage ss method to retrieve image url. getEduProviderLogo(eduProviderId)
  eduProviderId: string; //edu_providers.id
  eduProviderName?: string; // provider_programs join edu_providers on edu_provider_id
  description?: string;
  locations?: string[]; // provider_programs.locations. Saved as TEXT field in db but separate into list on DTO delimiter (~)
  programLength?: string;
  targetedJobRoles?: string[]; // delimited list of job roles. delimiter ~
  about?: string; // provider_programs.about Possibly use Quill to implement this
  tuition?: string; // provider_programs.tuition
  fees?: string; // provider_programs.fees
  costSummary?: string; // provider_programs.costSummary
  locationType?: LocationType | null; // provider_programs.locationType (enum LocationType)
  getStartedUrl?: string; // provider_programs.getStartedUrl
  faq?: { question: string; answer: string }[]; // provider_programs.faq as TEXT field parse response with JSON.parse, JSON.stringify
  pathways: EduProviderPathways[]; // provider_programs.pathways will need converted from string to list and each item cast into EduProviderPathways enum
};

// TODO: align with ICT Job Group Families
export enum EduProviderPathways {
  SoftwareDeveloper = "Software Development",
  ITCloudSupport = "Infrastructure and Operations",
  Cybersecurity = "Cybersecurity",
  DataAnalytics = "Data Science",
  BusinessMgmt = "Business and Management",
  ProfessionSkillsTraining = "Profession Skills Training",
  UXDesign = "Design and User Experience",
  QA_assurance = "Testing and Quality Assurance",
  ProgramManagement = "Program Management",
}

export enum EducationType {
  // TODO: Instead of creating a new enum. Let's use the existing EducationLevel enum in data/dtos/JobSeekerProfileCreationDTOs.ts
  K12 = "K12",
  College = "College",
}

export enum LocationType {
  InPerson = "In-Person",
  Online = "Online",
}

export const getEduProviderDetail = async (
  eduProviderId: string,
): Promise<ReadEduProviderDTO | null> => {
  const data = await prisma.edu_providers.findUnique({
    where: {
      id: eduProviderId,
    },
  });

  if (!data) return null; // Return null if the provider is not found

  // Transform and map the data to ReadEduProviderDTO
  const transformedData: ReadEduProviderDTO = {
    eduProviderId: data.id,
    eduLevel: data.edu_type ? (data.edu_type as EducationLevel) : undefined,
    providerName: data.name,
    logoUrl: data.logoUrl || "", // Assuming you need to add logic for generating logoUrl
    contactName: data.contact || undefined,
    contactEmail: data.contact_email || undefined,
    url: data.edu_url || undefined,
    mission: data.mission || undefined,
    providerDescription: data.providerDescription || undefined,
    setsApartStatement: data.setsApartStatement || undefined,
    screeningCriteria: data.screeningCriteria || undefined,
    recruitingSources: data.recruitingSources || undefined,
    programCount: data.programCount || undefined,
    cost: data.cost || undefined,
    isAdminReviewed: data.isAdminReviewed || false,
    isCoalitionMember: data.isCoalitionMember || false,
    createdBy: data.userId || undefined,
  };

  return transformedData;
};

export const getAllEduProvidersDetail = async (): Promise<
  ReadEduProviderDTO[] | null
> => {
  const data = await prisma.edu_providers.findMany({
    where: {
      isCoalitionMember: true,
    },
  });

  if (!data) return null; // Return null if the provider is not found

  // Transform and map the data to ReadEduProviderDTO
  const transformedData: ReadEduProviderDTO[] = data.map((provider) => ({
    eduProviderId: provider.id,
    eduLevel: provider.edu_type
      ? (provider.edu_type as EducationLevel)
      : undefined,
    providerName: provider.name,
    logoUrl: provider.logoUrl || "", // Assuming you need to add logic for generating logoUrl
    contactName: provider.contact || undefined,
    contactEmail: provider.contact_email || undefined,
    url: provider.edu_url || undefined,
    mission: provider.mission || undefined,
    providerDescription: provider.providerDescription || undefined,
    setsApartStatement: provider.setsApartStatement || undefined,
    screeningCriteria: provider.screeningCriteria || undefined,
    recruitingSources: provider.recruitingSources || undefined,
    programCount: provider.programCount || undefined,
    cost: provider.cost || undefined,
    isAdminReviewed: provider.isAdminReviewed || false,
    isCoalitionMember: provider.isCoalitionMember || false,
    createdBy: provider.userId || undefined,
  }));

  return transformedData;
};

// Overload signatures
export async function getProviderProgramCardView(
  pathway: EduProviderPathways,
): Promise<ReadEduProviderProgramCardDTO[]>;
export async function getProviderProgramCardView(
  eduProviderId: string,
): Promise<ReadEduProviderProgramCardDTO[]>;

// Implementation
export async function getProviderProgramCardView(
  param: EduProviderPathways | string,
): Promise<ReadEduProviderProgramCardDTO[]> {
  const isPathway =
    typeof param === "string" &&
    Object.values(EduProviderPathways).includes(param as EduProviderPathways);

  // Fetch all programs
  const data = await prisma.provider_programs.findMany({
    include: {
      Program: true, // Include related program details
      edu_provider: true, // Include related edu_provider details
    },
    where: isPathway
      ? undefined // No filtering on pathway at query level
      : { edu_provider_id: param as string }, // Filter by eduProviderId
  });

  // Transform and filter the data
  const programCards: ReadEduProviderProgramCardDTO[] = data
    .filter((program) => {
      if (isPathway) {
        if (!program.pathways) return false; // Skip if pathways field is null/undefined
        const pathwaysArray = program.pathways
          .split("~")
          .map((path) => path.trim());
        return pathwaysArray.includes(param as EduProviderPathways); // Filter programs matching the pathway
      }
      return true; // No additional filtering for eduProviderId
    })
    .map((program) => ({
      programId: program.training_program_id,
      programName: program.Program.title,
      logoUrl: program.edu_provider.logoUrl || "",
      eduProviderId: program.edu_provider_id,
      eduProviderName: program.edu_provider.name,
      eduLevel: isEnumValue(EducationLevel, program.eduLevel)
        ? (program.eduLevel as EducationLevel)
        : null,
      programLength: program.programLength || "",
      tuition: program.tuition || "",
      fees: program.fees || "",
      locationType: isEnumValue(LocationType, program.locationType)
        ? (program.locationType as LocationType)
        : null,
      pathway: program.pathways
        ? program.pathways
            .split("~")
            .map((path) => path.trim())
            .filter((path): path is EduProviderPathways =>
              isEnumValue(EduProviderPathways, path),
            )
        : [],
    }));

  return programCards;
}

export const getProviderProgramDetailView = async (
  trainingProgramId: string,
): Promise<ReadEduProviderProgramDetailDTO> => {
  // Fetch the provider program with related data
  const program = await prisma.provider_programs.findUnique({
    where: {
      training_program_id: trainingProgramId,
    },
    select: {
      training_program_id: true,
      about: true,
      tuition: true,
      fees: true,
      costSummary: true,
      locationType: true,
      programLength: true,
      getStartedUrl: true,
      faq: true,
      pathways: true,
      locations: true,
      edu_provider: {
        select: {
          id: true,
          name: true,
          logoUrl: true,
        },
      },
      Program: {
        select: {
          title: true,
        },
      },
    },
  });

  if (!program) {
    throw new Error("Program not found");
  }

  // Safe JSON parsing for FAQ
  let faq: { question: string; answer: string }[] = [];
  if (program.faq) {
    try {
      faq = JSON.parse(program.faq);
    } catch (error) {
      console.error("Failed to parse FAQ JSON:", error);
      faq = [];
    }
  }

  // Map the database fields to the DTO
  const dto: ReadEduProviderProgramDetailDTO = {
    programId: program.training_program_id,
    programName: program.Program.title,
    logoUrl: program.edu_provider.logoUrl || "",
    eduProviderId: program.edu_provider.id,
    eduProviderName: program.edu_provider.name,
    locations: program.locations
      ? program.locations.split("~").map((location) => location.trim())
      : [],
    about: program.about || "",
    tuition: program.tuition || undefined,
    fees: program.fees || undefined,
    costSummary: program.costSummary || undefined,
    locationType: isEnumValue(LocationType, program.locationType)
      ? (program.locationType as LocationType)
      : null,
    programLength: program.programLength || "",
    getStartedUrl: program.getStartedUrl || "",
    faq: faq,
    pathways: program.pathways
      ? program.pathways
          .split("~")
          .map((path) => path.trim())
          .filter((path): path is EduProviderPathways =>
            isEnumValue(EduProviderPathways, path),
          )
      : [],
  };

  return dto;
};

export const upsertTrainingProviderProgram = async (
  programDetail: PostEduProviderProgramDetailDTO,
) => {
  devLog("upsertTrainingProviderProgram > programDetail\n", programDetail);

  return prisma.$transaction(async (prisma) => {
    // find the general program name for the jobseeker education drop-down. If it doesn't exist create it.
    const generalProgram = await prisma.programs.upsert({
      where: {
        title: programDetail.programName,
      },
      update: {
        title: programDetail.programName,
      },
      create: {
        id: uuidv4(),
        title: programDetail.programName,
      },
    });

    // retrieve training_program_id
    const providerProgram = await prisma.provider_programs.findFirst({
      where: {
        edu_provider_id: programDetail.eduProviderId,
        program_id: generalProgram.id,
      },
    });

    // upsert provider program entry with training_program_id
    const updatedProviderProgram = await prisma.provider_programs.upsert({
      where: {
        training_program_id: providerProgram?.training_program_id || uuidv4(),
      },
      update: {
        program_id: generalProgram.id,
        edu_provider_id: programDetail.eduProviderId,
        description: programDetail.description,
        targetedJobRoles: programDetail.targetedJobRoles?.join("~") ?? "", // omitted on request by AddProviderProgramsFrom.tsx when a new entry
        locations: programDetail.locations?.join("~"),
        programLength: programDetail.programLength,
        about: programDetail.about,
        tuition: programDetail.tuition,
        fees: programDetail.fees,
        costSummary: programDetail.costSummary,
        locationType: programDetail.locationType ?? "", // omitted
        getStartedUrl: programDetail.getStartedUrl,
        faq: JSON.stringify(programDetail.faq || []),
        pathways: programDetail.pathways?.join(",") || "", // omitted
      },
      create: {
        training_program_id: uuidv4(),
        program_id: generalProgram.id,
        edu_provider_id: programDetail.eduProviderId,
        description: programDetail.description,
        targetedJobRoles: programDetail.targetedJobRoles?.join("~") ?? "",
        locations: programDetail.locations?.join("~"),
        programLength: programDetail.programLength,
        about: programDetail.about,
        tuition: programDetail.tuition,
        fees: programDetail.fees,
        costSummary: programDetail.costSummary,
        locationType: programDetail?.locationType || "",
        getStartedUrl: programDetail.getStartedUrl,
        faq: JSON.stringify(programDetail.faq || []),
        pathways: programDetail.pathways?.join("~") || "",
      },
      select: {
        training_program_id: true,
        about: true,
        tuition: true,
        fees: true,
        costSummary: true,
        locationType: true,
        programLength: true,
        getStartedUrl: true,
        faq: true,
        pathways: true,
        locations: true,
        targetedJobRoles: true,
        edu_provider: {
          select: {
            id: true,
            name: true,
            logoUrl: true,
          },
        },
        Program: {
          select: {
            title: true,
          },
        },
      },
    });

    // Safe JSON parsing for FAQ
    let faq: { question: string; answer: string }[] = [];
    if (updatedProviderProgram.faq) {
      try {
        faq = JSON.parse(updatedProviderProgram.faq);
      } catch (error) {
        console.error("Failed to parse FAQ JSON:", error);
        faq = [];
      }
    }

    // Map the database fields to the DTO
    const dto: ReadEduProviderProgramDetailDTO = {
      programId: updatedProviderProgram.training_program_id,
      programName: updatedProviderProgram.Program.title,
      logoUrl: updatedProviderProgram.edu_provider.logoUrl || "",
      eduProviderId: updatedProviderProgram.edu_provider.id,
      eduProviderName: updatedProviderProgram.edu_provider.name,
      locations: updatedProviderProgram.locations
        ? updatedProviderProgram.locations
            .split("~")
            .map((location) => location.trim())
        : [],
      about: updatedProviderProgram.about || "",
      tuition: updatedProviderProgram.tuition || undefined,
      fees: updatedProviderProgram.fees || undefined,
      costSummary: updatedProviderProgram.costSummary || undefined,
      locationType: isEnumValue(
        LocationType,
        updatedProviderProgram.locationType,
      )
        ? (updatedProviderProgram.locationType as LocationType)
        : null,
      programLength: updatedProviderProgram.programLength || "",
      getStartedUrl: updatedProviderProgram.getStartedUrl || "",
      targetedJobRoles: updatedProviderProgram?.targetedJobRoles?.split("~"), // comma separated from user store with ~ delimiter
      faq: faq,
      pathways: updatedProviderProgram.pathways
        ? updatedProviderProgram.pathways
            .split("~")
            .map((path) => path.trim())
            .filter((path): path is EduProviderPathways =>
              isEnumValue(EduProviderPathways, path),
            )
        : [],
    };

    return dto;
  });
};
// //Redundant, already have a delete provider program in /lib/admin/eduProviderPartners line 202
// export const deleteTrainingProviderProgram = async (providerProgramId: string) => {
//  const deletedProviderProgram = await prisma.provider_programs.delete({
//      where: {
//          training_program_id: providerProgramId
//      },
//      select: {
//          training_program_id: true,
//          about: true,
//          tuition: true,
//          fees: true,
//          costSummary: true,
//          locationType: true,
//          programLength: true,
//          getStartedUrl: true,
//          faq: true,
//          pathways: true,
//          locations: true,
//          edu_provider: {
//              select: {
//                  id: true,
//                  name: true,
//                  logoUrl: true,
//              },
//          },
//          Program: {
//              select: {
//                  title: true,
//              },
//          },
//      },
//  });

//     // Safe JSON parsing for FAQ
//     let faq: { question: string; answer: string }[] = [];
//     if (deletedProviderProgram.faq) {
//         try {
//             faq = JSON.parse(deletedProviderProgram.faq);
//         } catch (error) {
//             console.error('Failed to parse FAQ JSON:', error);
//             faq = [];
//         }
//     }

//     // Map the database fields to the DTO
//     const dto: ReadEduProviderProgramDetailDTO = {
//         programId: deletedProviderProgram.training_program_id,
//         programName: deletedProviderProgram.Program.title,
//         logoUrl: deletedProviderProgram.edu_provider.logoUrl || '',
//         eduProviderId: deletedProviderProgram.edu_provider.id,
//         eduProviderName: deletedProviderProgram.edu_provider.name,
//         locations: deletedProviderProgram.locations
//           ? deletedProviderProgram.locations.split('~').map(location => location.trim())
//           : [],
//         about: deletedProviderProgram.about || '',
//         tuition: deletedProviderProgram.tuition || undefined,
//         fees: deletedProviderProgram.fees || undefined,
//         costSummary: deletedProviderProgram.costSummary || undefined,
//         locationType: isEnumValue(LocationType, deletedProviderProgram.locationType) ? deletedProviderProgram.locationType as LocationType : null,
//         programLength: deletedProviderProgram.programLength || '',
//         getStartedUrl: deletedProviderProgram.getStartedUrl || '',
//         faq: faq,
//         pathways: deletedProviderProgram.pathways
//           ? deletedProviderProgram.pathways
//             .split('~')
//             .map(path => path.trim())
//             .filter((path): path is EduProviderPathways =>
//               isEnumValue(EduProviderPathways, path)
//             )
//           : [],
//     };

//     return dto;
// }

export function isEnumValue<
  T extends { [key: string]: string | number | null },
>(enumObj: T, value: string | number | null): value is T[keyof T] {
  if (value === null || value === undefined || value === "") return false;
  return Object.values(enumObj).includes(value);
}
