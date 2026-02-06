import { Prisma, PrismaClient } from "@prisma/client";
import {
  EducationLevel,
  HighestCompletedEducationLevel,
  ProgramEnrollmentStatus,
} from "@/data/dtos/JobSeekerProfileCreationDTOs";
import { CareerPrepTrack, PoolCategories } from "@/app/lib/poolAssignment";
import getPrismaClient from "@/app/lib/prismaClient.mjs";
import { auth } from "@/auth";
import { devLog } from "@/app/lib/utils";
import TransactionClient = Prisma.TransactionClient;
import { Role } from "@/data/dtos/UserInfoDTO";
import { JobStatus } from "../jobseekerJobTracking";
import { CareerPrepGridData } from "@/app/ui/components/careerPrep/CareerPrepDataGrid";

const prisma: PrismaClient = getPrismaClient();

/**
 * Enumeration representing different time frames until completion.
 * Possible values include:
 * - NA: Not applicable
 * - ZeroToThreeMonths: Within the range of 0 to 3 months
 * - ThreeToSixMonths: Within the range of 3 to 6 months
 * - SixToNineMonths: Within the range of 6 to 9 months
 * - NineToTwelveMonths: Within the range of 9 to 12 months
 * - TwelvePlusMonths: More than 12 months to completion
 */
export enum TimeUntilCompletion {
  NA = "N/A",
  ZeroToThreeMonths = "0-3 months",
  ThreeToSixMonths = "3-6 months",
  SixToNineMonths = "6-9 months",
  NineToTwelveMonths = "9-12 months",
  TwelvePlusMonths = "12+ months",
}

/**
 * Represents the status of a technical certificate.
 * - NA: Not Applicable
 * - InProgress: Certificate is in progress
 * - Obtained: Certificate has been obtained
 */
export enum TechCertificateStatus {
  NA = "N/A",
  InProgress = "In Progress",
  Obtained = "Obtained",
}

/**
 * Enum representing the different status options for a career preparation process.
 * @enum {string}
 */
export enum CareerPrepStatus {
  CreatingPlan = "Creating Plan",
  PlanCreated = "Plan Created",
  MeetingScheduled = "Meeting Scheduled",
  MetCareerNavigator = "Met Career Navigator",
  Applied = "Applied",
  Admitted = "Admitted",
  Rejected = "Rejected",
  Enrolled = "Enrolled",
  Active = "Active",
  Inactive = "Inactive",
  Withdrawn = "Withdrawn", // additional option from what was given.
  Placed = "Placed", // added in light of filters for stats requested by Bethany.
  Completed = "Completed", // Student has marked their readiness packet as complete, signals Career Nav for manual review
  JobReady = "Job-Ready", // After student marks completion Career Navigator manually assigns Job Ready after satisfactory review.
}

/**
 * Represents data transfer object for Admin Career Prep.
 * This will be used to load all Jobseekers who have completed an Assessment for Career Prep
 */
export interface AdminCareerPrepDTO {
  students: CareerPrepJobseekerCardViewDTO[];
}

/**
 * Represents a summary of a student including their details, meetings, and notes.
 * This will lazy load on expanding card view of student.
 * @interface
 */
export interface StudentSummary {
  studentDetail?: CareerPrepJobseekerDetailViewDTO;
  generalNotes: NoteDTO[] | null; // will filter notes by NoteType on backend
  meetingNotes: NoteDTO[] | null;
  followUpNotes: NoteDTO[] | null;
}

/**
 * Retrieves a summary of career preparation information for a specific jobseeker.
 * Including student details and notes filtered by NoteType
 * @param {string} jobseekerId - The ID of the jobseeker to retrieve information for
 * @returns {Promise<StudentSummary | null>} A Promise that resolves to a StudentSummary object
 */
export const getCareerPrepStudentSummary = async (
  jobseekerId: string,
): Promise<StudentSummary | null> => {
  const studentDetail = await getCareerPrepStudentDetailView(jobseekerId);
  const notes = await getCareerPrepStudentNotes(jobseekerId);
  // Handle error case for student detail
  if (!studentDetail.success) {
    console.error(studentDetail.error);
    return null;
  }

  return {
    studentDetail: studentDetail.data,
    generalNotes: notes.generalNotes,
    meetingNotes: notes.meetingNotes,
    followUpNotes: notes.followUpNotes,
  };
};

/**
 * Interface representing a data transfer object for Jobseeker Card View in Career Prep module.
 * @interface CareerPrepJobseekerCardViewDTO
 */
export interface CareerPrepJobseekerCardViewDTO {
  jobseekerId: string;
  firstName: string;
  lastName: string;
  pronouns: string;
  assignedCareerPrepTrack: CareerPrepTrack | null;
  recommendedCareerPrepTrack: CareerPrepTrack | null;
  careerPrepAssessmentDate: Date;
  careerPrepEnrollmentStatus: CareerPrepStatus;
  careerPrepExpectedEndDate: Date | null;
  expectedEduCompletion: TimeUntilCompletion;
  assignedPool: PoolCategories;
  // techAssessmentAvg: number;
  // durableSkillAssessmentAvg: number;
  // brandingAssessmentAvg: number;
}

export const getAllCareerPrepStudentsCardView = async (): Promise<
  CareerPrepJobseekerCardViewDTO[] | null
> => {
  try {
    const data = await prisma.careerPrepAssessment.findMany({
      select: selectCareerPrepStudentCardView,
    });
    // Transform the data to match the CareerPrepJobseekerCardViewDTO structure
    const transformedData: CareerPrepJobseekerCardViewDTO[] = data.map(
      (item) => ({
        jobseekerId: item.jobseekerId,
        firstName: item.Jobseeker?.users?.first_name || "",
        lastName: item.Jobseeker?.users?.last_name || "",
        pronouns: item.pronouns,
        assignedCareerPrepTrack: item.CaseMgmt
          ?.AssignedCareerPrepTrack as CareerPrepTrack,
        recommendedCareerPrepTrack: item.Jobseeker
          .careerPrepTrackRecommendation as CareerPrepTrack,
        careerPrepAssessmentDate: item.assessmentDate,
        careerPrepEnrollmentStatus: item.CaseMgmt
          ?.prepEnrollmentStatus as CareerPrepStatus,
        careerPrepExpectedEndDate: item.CaseMgmt?.prepExpectedEndDate || null,
        expectedEduCompletion:
          item.expectedEduCompletion as TimeUntilCompletion,
        assignedPool:
          (item.Jobseeker?.assignedPool as PoolCategories) ||
          PoolCategories.None,
      }),
    );
    return transformedData;
  } catch (e) {
    console.error("Error fetching career prep students card view:", e);
    return null;
  } finally {
    prisma.$disconnect();
  }
};
//unused
export const getCareerPrepStudentsCardViewByCaseManagerSession =
  async (): Promise<CareerPrepGridData[]> => {
    try {
      const session = await auth();
      const data = await prisma.careerPrepAssessment.findMany({
        select: selectCareerPrepStudentCardView,
        where: {
          CaseMgmt: {
            CaseManager: {
              id: session?.user.id,
            },
          },
        },
      });
      devLog("career prep card view", data);
      // Transform the data to match the CareerPrepJobseekerCardViewDTO structure
      const transformedData: CareerPrepGridData[] = data.map((item) => ({
        AppearOnShowCase: item.Jobseeker.prescreened,
        CybersecurityRating: item.CybersecurityRating,
        DataAnalyticsRating: item.DataAnalyticsRating,
        SoftwareDevRating: item.SoftwareDevRating,
        DurableSkillsRating: item.DurableSkillsRating,
        ITCloudRating: item.ITCloudRating,
        BrandingRating: item.BrandingRating,
        jobseeker_id: item.jobseekerId,
        first_name: item.Jobseeker?.users?.first_name || "",
        HighestEdLevel:
          item.Jobseeker.highest_level_of_study_completed ?? "Unknown",
        last_name: item.Jobseeker?.users?.last_name || "",
        "Pathway Title": item.Jobseeker.pathways?.pathway_title ?? "None",
        email: item.Jobseeker.users.email,
        EnrollmentDate: item.CaseMgmt?.createdAt ?? new Date(),
        JobseekerUpdatedAt: item.Jobseeker?.updatedAt ?? new Date("1/1/1979"),
        JobseekerCreatedAt: item.Jobseeker?.createdAt,
        pronouns: item.pronouns,
        careerPrepTrackRecommendation: item.Jobseeker
          .careerPrepTrackRecommendation as CareerPrepTrack,
        assignedCareerPrepTrack: item.CaseMgmt
          ?.AssignedCareerPrepTrack as CareerPrepTrack,
        careerPrepAssessmentDate: item.assessmentDate,
        user_id: item.Jobseeker.users.id,
        "CP Enrollment Status": item.CaseMgmt
          ?.prepEnrollmentStatus as CareerPrepStatus,
        careerPrepExpectedEndDate: item.CaseMgmt?.prepExpectedEndDate || null,
        expectedEduCompletion:
          item.expectedEduCompletion as TimeUntilCompletion,
        "Pool Type":
          (item.Jobseeker?.assignedPool as PoolCategories) ||
          PoolCategories.None,
      }));
      return transformedData;
    } catch (e) {
      console.error("Error fetching career prep students card view:", e);
      return [];
    } finally {
      prisma.$disconnect();
    }
  };
/**
 * Asynchronously retrieves a list of unmanaged Career Prep students.
 * Returns a Promise that resolves to an array of CareerPrepJobseekerCardViewDTO objects.
 *
 * The function queries the database to find Career Prep assessments that have not been assigned a Case Manager. It then transforms the data into a list of CareerPre
 *pJobseekerCardViewDTO objects containing relevant information about each student's career preparation status.
 *
 * @return {Promise<CareerPrepJobseekerCardViewDTO[]>} A Promise resolving to an array of CareerPrepJobseekerCardViewDTO objects representing unmanaged Career Prep students.
 */
export const getUnManagedCareerPrepStudents = async (): Promise<
  CareerPrepGridData[]
> => {
  try {
    const assessmentsWithoutCaseMgmt =
      await prisma.careerPrepAssessment.findMany({
        select: selectCareerPrepStudentCardView,
        where: {
          CaseMgmt: {
            CaseManager: null,
          },
        },
      });
    const transformedData: CareerPrepGridData[] =
      assessmentsWithoutCaseMgmt.map((item) => ({
        AppearOnShowCase: item.Jobseeker.prescreened,
        CybersecurityRating: item.CybersecurityRating,
        DataAnalyticsRating: item.DataAnalyticsRating,
        SoftwareDevRating: item.SoftwareDevRating,
        DurableSkillsRating: item.DurableSkillsRating,
        ITCloudRating: item.ITCloudRating,
        BrandingRating: item.BrandingRating,
        jobseeker_id: item.jobseekerId,
        first_name: item.Jobseeker?.users?.first_name || "",
        HighestEdLevel:
          item.Jobseeker.highest_level_of_study_completed ?? "Unknown",
        last_name: item.Jobseeker?.users?.last_name || "",
        "Pathway Title": item.Jobseeker.pathways?.pathway_title ?? "None",
        email: item.Jobseeker.users.email,
        EnrollmentDate: item.CaseMgmt?.createdAt ?? new Date(),
        JobseekerUpdatedAt: item.Jobseeker?.updatedAt ?? new Date("1/1/1979"),
        JobseekerCreatedAt: item.Jobseeker?.createdAt,
        pronouns: item.pronouns,
        careerPrepTrackRecommendation: item.Jobseeker
          .careerPrepTrackRecommendation as CareerPrepTrack,
        assignedCareerPrepTrack: item.CaseMgmt
          ?.AssignedCareerPrepTrack as CareerPrepTrack,
        careerPrepAssessmentDate: item.assessmentDate,
        user_id: item.Jobseeker.users.id,
        "CP Enrollment Status": item.CaseMgmt
          ?.prepEnrollmentStatus as CareerPrepStatus,
        careerPrepExpectedEndDate: item.CaseMgmt?.prepExpectedEndDate || null,
        expectedEduCompletion:
          item.expectedEduCompletion as TimeUntilCompletion,
        "Pool Type":
          (item.Jobseeker?.assignedPool as PoolCategories) ||
          PoolCategories.None,
      }));
    return transformedData;
  } catch (error) {
    console.error(error);
    return [];
  }
};
export const getAllJobSeekersForCareerPrepHomePage = async (): Promise<
  CareerPrepGridData[]
> => {
  try {
    const JobSeekers = await prisma.jobseekers.findMany({
      include: {
        CareerPrepAssessment: {
          include: {
            CybersecurityRating: true,
            DataAnalyticsRating: true,
            ITCloudRating: true,
            CaseMgmt: true,
            SoftwareDevRating: true,
            DurableSkillsRating: true,
            BrandingRating: true,
          },
        },
        users: true,
      },
    });
    const transformedData: CareerPrepGridData[] = JobSeekers.map((item) => ({
      AppearOnShowCase: item.prescreened,
      CybersecurityRating: item.CareerPrepAssessment.flatMap(
        (cpa) => cpa.CybersecurityRating,
      ),
      DataAnalyticsRating: item.CareerPrepAssessment.flatMap(
        (cpa) => cpa.DataAnalyticsRating,
      ),
      SoftwareDevRating: item.CareerPrepAssessment.flatMap(
        (cpa) => cpa.SoftwareDevRating,
      ),
      DurableSkillsRating: item.CareerPrepAssessment.flatMap(
        (cpa) => cpa.DurableSkillsRating,
      ),
      ITCloudRating: item.CareerPrepAssessment.flatMap(
        (cpa) => cpa.ITCloudRating,
      ),
      BrandingRating: item.CareerPrepAssessment.flatMap(
        (cpa) => cpa.BrandingRating,
      ),
      jobseeker_id: item.jobseeker_id,
      first_name: item.users?.first_name || "",
      HighestEdLevel: item.highest_level_of_study_completed ?? "Unknown",
      last_name: item.users?.last_name || "",
      email: item.users.email,
      careerPrepTrackRecommendation:
        item.careerPrepTrackRecommendation as CareerPrepTrack,
      user_id: item.users.id,
      "CP Enrollment Status": item.CareerPrepAssessment.pop()?.CaseMgmt
        ?.prepEnrollmentStatus as CareerPrepStatus,
      "Pool Type": (item.assignedPool as PoolCategories) || PoolCategories.None,
    }));
    return transformedData;
  } catch (error) {
    console.error(error);
    return [];
  }
};
export const getAllPreScreenedCareerPrepStudents = async (): Promise<
  CareerPrepGridData[]
> => {
  try {
    const assessmentsWithoutCaseMgmt =
      await prisma.careerPrepAssessment.findMany({
        select: selectCareerPrepStudentCardView,
        where: {
          Jobseeker: {
            prescreened: true,
          },
        },
      });
    const transformedData: CareerPrepGridData[] =
      assessmentsWithoutCaseMgmt.map((item) => ({
        AppearOnShowCase: item.Jobseeker.prescreened,
        CybersecurityRating: item.CybersecurityRating,
        DataAnalyticsRating: item.DataAnalyticsRating,
        SoftwareDevRating: item.SoftwareDevRating,
        DurableSkillsRating: item.DurableSkillsRating,
        ITCloudRating: item.ITCloudRating,
        BrandingRating: item.BrandingRating,
        jobseeker_id: item.jobseekerId,
        first_name: item.Jobseeker?.users?.first_name || "",
        HighestEdLevel:
          item.Jobseeker.highest_level_of_study_completed ?? "Unknown",
        last_name: item.Jobseeker?.users?.last_name || "",
        "Pathway Title": item.Jobseeker.pathways?.pathway_title ?? "None",
        email: item.Jobseeker.users.email,
        EnrollmentDate: item.CaseMgmt?.createdAt ?? new Date(),
        JobseekerUpdatedAt: item.Jobseeker?.updatedAt ?? new Date("1/1/1979"),
        JobseekerCreatedAt: item.Jobseeker?.createdAt,
        pronouns: item.pronouns,
        careerPrepTrackRecommendation: item.Jobseeker
          .careerPrepTrackRecommendation as CareerPrepTrack,
        assignedCareerPrepTrack: item.CaseMgmt
          ?.AssignedCareerPrepTrack as CareerPrepTrack,
        careerPrepAssessmentDate: item.assessmentDate,
        user_id: item.Jobseeker.users.id,
        "CP Enrollment Status": item.CaseMgmt
          ?.prepEnrollmentStatus as CareerPrepStatus,
        careerPrepExpectedEndDate: item.CaseMgmt?.prepExpectedEndDate || null,
        expectedEduCompletion:
          item.expectedEduCompletion as TimeUntilCompletion,
        "Pool Type":
          (item.Jobseeker?.assignedPool as PoolCategories) ||
          PoolCategories.None,
      }));
    return transformedData;
  } catch (error) {
    console.error(error);
    return [];
  }

  return [];
};

export async function setPresreenedStatus(
  jobsekerId: string,
  prescreened: boolean,
) {
  try {
    const result = await prisma.jobseekers.update({
      where: {
        jobseeker_id: jobsekerId,
      },
      data: {
        prescreened: prescreened,
      },
    });
    return result;
  } catch (error) {
    console.error(error);
  }
}

/**
 * Assigns the authenticated user as the case manager for a specific jobseeker.
 *
 * @param {string} jobseekerId - The ID of the jobseeker to assign a case manager to.
 * @returns {Promise<{ success: true, status: 200 } | null>} A Promise that resolves to an object indicating the success status of the operation or null if an error occurs.
 */
export const selfAssignAsCaseManager = async (
  jobseekerId: string,
): Promise<{ success: boolean; status: number }> => {
  const session = await auth();
  try {
    await prisma.caseMgmt.update({
      where: {
        jobseekerId: jobseekerId,
      },
      data: {
        CaseManager: {
          connect: {
            id: session?.user.id,
          },
        },
      },
    });
    return { success: true, status: 200 };
  } catch (e) {
    console.error("failed to assign case manager", e);
    return { success: false, status: 500 };
  }
};

export const getAllCareerNavigators = async () => {
  try {
    const users = await prisma.user.findMany({
      select: {
        email: true,
        role: true,
        first_name: true,
        last_name: true,
      },
    });
    return users.filter((user) => user.role.includes(Role.CASE_MANAGER));
  } catch (error) {
    console.error(error);
  }
};

export const getCareerPrepStudentDetailView = async (jobseekerId: string) => {
  try {
    const data = await prisma.careerPrepAssessment.findUnique({
      where: {
        jobseekerId: jobseekerId,
      },
      select: selectCareerPrepStudentDetailView,
    });

    const jobseekerData = await prisma.jobseekers.findUnique({
      select: {
        careerPrepTrackRecommendation: true,
      },
      where: {
        jobseeker_id: jobseekerId,
      },
    });

    if (!data) {
      return {
        success: false,
        error: "Career Prep student not found.",
        status: 404,
      };
    }
    devLog("StudentDetailView", data);
    const transformedData: CareerPrepJobseekerDetailViewDTO = {
      jobseekerId: data.jobseekerId,
      assessmentDate: data.assessmentDate.toISOString(),
      recommendedCareerPrepTrack:
        jobseekerData?.careerPrepTrackRecommendation as CareerPrepTrack,
      assignedCareerPrepTrack: data.CaseMgmt
        ?.AssignedCareerPrepTrack as CareerPrepTrack,
      prepEnrollmentStatus: data.CaseMgmt
        ?.prepEnrollmentStatus as CareerPrepStatus,
      prepStartDate: data.CaseMgmt?.prepStartDate?.toISOString(),
      prescreened: data.Jobseeker.prescreened,
      prepExpectedEndDate: data.CaseMgmt?.prepExpectedEndDate?.toISOString(),
      prepActualEndDate: data.CaseMgmt?.prepActualEndDate?.toISOString(),
      firstName: data.Jobseeker?.users?.first_name!,
      lastName: data.Jobseeker?.users?.last_name!,
      pronouns: data.pronouns,
      emailAddress: data.Jobseeker?.users.email!,
      pathway: data?.interestPathway ?? "",
      education: data.Jobseeker
        ?.highest_level_of_study_completed as HighestCompletedEducationLevel,
      eduProviders: data.Jobseeker?.jobseeker_education.map((edData) => ({
        partnerTrainingProvider: edData.eduProviders.name!,
        trainingProgramTitle: edData?.program?.title!,
        educationLevel: edData.edLevel as EducationLevel,
        status: edData.enrollmentStatus as ProgramEnrollmentStatus,
      })),
      expectedEduCompletion: data?.expectedEduCompletion as TimeUntilCompletion,
      technicalCertificates: data.Jobseeker?.certificates.map((cert) => ({
        name: cert.name,
      })),
      portfolio: data.Jobseeker?.portfolio_url ?? "",
      linkedin: data.Jobseeker?.linkedin_url ?? "",
      applicationExperience: data.experienceWithApplying,
      interviewExperience: data.experienceWithInterview,
      poolAssignment: data.Jobseeker?.assignedPool as PoolCategories,
    };
    return { success: true, data: transformedData };
  } catch (e) {
    console.error("Unable to retrieve student detail view", e);
    return {
      success: false,
      error: "An unexpected error occurred",
      status: 500,
    };
  }
};
export const updateCareerPrepStudentDetailview = async (
  jobseekerId: string, // eslint-disable-line @typescript-eslint/no-unused-vars
  data: CareerPrepJobseekerDetailViewDTO, // eslint-disable-line @typescript-eslint/no-unused-vars
) => {
  //TODO
  console.log("This Needs to be written");
};

export const updateAssignedTrack = async (
  jobseekerId: string,
  track: CareerPrepTrack,
) => {
  try {
    const results = await prisma.caseMgmt.update({
      where: {
        jobseekerId: jobseekerId,
      },
      data: {
        AssignedCareerPrepTrack: track,
      },
    });
    return results;
  } catch (e) {
    console.error(e);
  }
};

/**
 * Select statement to retrieve data for Career Prep Student Card.
 * It contains various properties to collect data for CareerPrepJobseekerCardViewDTO[].
 */
const selectCareerPrepStudentCardView /*: Prisma.CareerPrepAssessmentSelect*/ =
  {
    // initial table CareerPrepAssessment
    jobseekerId: true,
    pronouns: true,
    assessmentDate: true,
    expectedEduCompletion: true,
    CybersecurityRating: true,
    DataAnalyticsRating: true,
    ITCloudRating: true,
    SoftwareDevRating: true,
    DurableSkillsRating: true,
    BrandingRating: true,
    CaseMgmt: {
      select: {
        prepEnrollmentStatus: true,
        prepExpectedEndDate: true,
        AssignedCareerPrepTrack: true,
        createdAt: true,
      },
    },
    Jobseeker: {
      select: {
        assignedPool: true,
        careerPrepTrackRecommendation: true,
        highest_level_of_study_completed: true,
        prescreened: true,
        createdAt: true,
        updatedAt: true,
        users: {
          select: {
            first_name: true,
            last_name: true,
            email: true,
            id: true,
          },
        },
        pathways: {
          select: {
            pathway_title: true,
          },
        },
      },
    },
  };

/**
 * Asynchronously updates the career preparation status card view for a job seeker.
 *
 * @param {string} jobseekerId - The unique identifier for the job seeker.
 * @param {CareerPrepStatus} [status] - The new career preparation status for the job seeker.
 *
 * @returns {Promise<{ status: CareerPrepStatus, expectedEndDate: Date | null } | null>} A promise that resolves with an object containing the updated status and expected end date, or
 * null if an error occurs.
 */
export const updateCareerPrepStatusCardView = async (
  jobseekerId: string,
  status?: CareerPrepStatus,
): Promise<{
  status: CareerPrepStatus;
  expectedEndDate: Date | null;
} | null> => {
  try {
    const data = await prisma.careerPrepAssessment.findUnique({
      where: {
        jobseekerId: jobseekerId,
      },
      select: selectCareerPrepStudentCardView,
    });
    const studentStatus = await prisma.caseMgmt.upsert({
      where: {
        jobseekerId: jobseekerId,
      },
      update: {
        ...(status ? { prepEnrollmentStatus: status } : {}),
      },
      create: {
        ...(status
          ? { prepEnrollmentStatus: status }
          : { prepEnrollmentStatus: CareerPrepStatus.Applied }),
        careerPrepTrack: data?.Jobseeker.careerPrepTrackRecommendation!,
        PrepAssessment: {
          connect: {
            jobseekerId: jobseekerId,
          },
        },
        // CaseManager: {
        //   connect: {
        //     id: session?.user.id!,
        //   },
        // },
      },
    });
    return {
      status: studentStatus.prepEnrollmentStatus as CareerPrepStatus,
      expectedEndDate: studentStatus.prepExpectedEndDate,
    };
  } catch (e) {
    console.error("Could not update student card view", e);
    return null;
  }
};

/**
 * Transactional wrapper for updating the career preparation status card view for a job seeker.
 *
 * @param {TransactionClient} tx - The Prisma transaction client used for database operations.
 * @param {string} jobseekerId - The unique identifier for the job seeker.
 * @param {CareerPrepStatus} [status] - The new career preparation status for the job seeker.
 *
 * @returns {Promise<{ status: CareerPrepStatus; expectedEndDate: Date | null } | null>}
 * A promise that resolves with an object containing the updated status and expected end date,
 * or null if an error occurs.
 *
 * @description
 * This function must be invoked within a Prisma.$transaction callback to ensure
 * the transaction context is maintained. Using the global Prisma client instead of
 * the transaction client (tx) may lead to transaction errors.
 */
export const updateCareerPrepStatusCardViewTx = async (
  tx: TransactionClient,
  jobseekerId: string,
  status?: CareerPrepStatus,
): Promise<{
  status: CareerPrepStatus;
  expectedEndDate: Date | null;
} | null> => {
  try {
    const data = await tx.careerPrepAssessment.findUnique({
      where: {
        jobseekerId: jobseekerId,
      },
      select: selectCareerPrepStudentCardView,
    });
    const studentStatus = await tx.caseMgmt.upsert({
      where: {
        jobseekerId: jobseekerId,
      },
      update: {
        ...(status ? { prepEnrollmentStatus: status } : {}),
      },
      create: {
        ...(status
          ? { prepEnrollmentStatus: status }
          : { prepEnrollmentStatus: CareerPrepStatus.Applied }),
        careerPrepTrack: data?.Jobseeker.careerPrepTrackRecommendation!,
        PrepAssessment: {
          connect: {
            jobseekerId: jobseekerId,
          },
        },
        // CaseManager: {
        //   connect: {
        //     id: session?.user.id!,
        //   },
        // },
      },
    });
    return {
      status: studentStatus.prepEnrollmentStatus as CareerPrepStatus,
      expectedEndDate: studentStatus.prepExpectedEndDate,
    };
  } catch (e) {
    console.error("Could not update student card view", e);
    return null;
  }
};

export async function getCareerPrepStatus(jobseeker_id: string) {
  try {
    if (jobseeker_id == "") return undefined;
    const result = await prisma.caseMgmt.findUnique({
      where: { jobseekerId: jobseeker_id },
      include: { CaseManager: true },
    });

    const jobseekerResult = await prisma.jobseekers.findUnique({
      where: { jobseeker_id: jobseeker_id },
      select: {
        careerPrepTrackRecommendation: true,
      },
    });

    return {
      enrollment: result?.prepEnrollmentStatus as CareerPrepStatus,
      AutoRecommendedTrack:
        jobseekerResult?.careerPrepTrackRecommendation as CareerPrepTrack,
      AssignedTrack: result?.AssignedCareerPrepTrack as CareerPrepTrack,
      CaseManger: result?.CaseManager,
    };
  } catch (error) {
    console.error(error);
  }
}

/**
 * Select statement to retrieve Career Prep student details.
 * Accessed through prisma.careerPrepAssessment model.
 */
const selectCareerPrepStudentDetailView /*: Prisma.CareerPrepAssessmentSelect*/ =
  {
    jobseekerId: true,
    assessmentDate: true,
    interestPathway: true,
    pronouns: true,
    expectedEduCompletion: true,
    experienceWithApplying: true,
    experienceWithInterview: true,
    CaseMgmt: {
      select: {
        prepEnrollmentStatus: true,
        prepStartDate: true,
        prepExpectedEndDate: true,
        prepActualEndDate: true,
        careerPrepTrack: true,
        AssignedCareerPrepTrack: true,
      },
    },
    Jobseeker: {
      select: {
        highest_level_of_study_completed: true,
        portfolio_url: true,
        linkedin_url: true,
        assignedPool: true,
        prescreened: true,
        careerPrepTrackRecommendation: true,
        users: {
          select: {
            first_name: true,
            last_name: true,
            email: true,
          },
        },
        jobseeker_education: {
          select: {
            edLevel: true,
            enrollmentStatus: true,
            eduProviders: {
              select: {
                name: true,
              },
            },
            program: {
              select: {
                title: true,
              },
            },
          },
        },
        certificates: {
          select: {
            name: true,
            status: true,
          },
        },
      },
    },
  };

/**
 * Represents the detailed view of a jobseeker in the Career Prep program.
 * @interface CareerPrepJobseekerDetailViewDTO
 */
export interface CareerPrepJobseekerDetailViewDTO {
  jobseekerId: string;
  assessmentDate: string; //DateIsoString
  prepEnrollmentStatus: CareerPrepStatus;
  prepStartDate?: string; //DateIsoString
  recommendedCareerPrepTrack: CareerPrepTrack | null;
  assignedCareerPrepTrack: CareerPrepTrack | null;
  prepExpectedEndDate?: string; // DateIsoString System startDate + Track Length.
  prepActualEndDate?: string; // DateIsoString Entered manually
  firstName: string;
  lastName: string;
  pronouns: string;
  emailAddress: string;
  pathway: string;
  prescreened: boolean;
  education: HighestCompletedEducationLevel;
  eduProviders?: PartnerTrainingProvider[];
  expectedEduCompletion: TimeUntilCompletion;
  technicalCertificates: { name: string }[]; // resume: omitted but will be retrieved with blob storage function call getResumeUrl().
  // coverLetter: omitted but will be retrieved with blob storage function call getCoverLetterUrl().
  portfolio: string; // URL
  linkedin: string; // URL
  applicationExperience: boolean;
  interviewExperience: boolean;
  poolAssignment: PoolCategories;
}

/**
 * Interface representing a partner training provider.
 * @interface
 */
export interface PartnerTrainingProvider {
  partnerTrainingProvider: string;
  trainingProgramTitle: string;
  educationLevel: EducationLevel; // differentiate between degree and nondegree education/training
  status: ProgramEnrollmentStatus;
}

export type NoteDTO = {
  id: string;
  jobseekerId: string;
  createdBy: string;
  noteType: NoteType;
  noteContent: string;
  createdAt: string;
  updatedAt: string;
  date?: string | null;
  authorName: string;
};
export type CreateNoteDTO = {
  jobseekerId: string;
  noteType: NoteType;
  noteContent: string;
  updatedDate?: Date;
};
export type UpdateNoteDTO = {
  noteId: string;
  noteType: NoteType;
  noteContent: string;
  updatedDate?: Date;
};

export type CategorizedNotes = {
  generalNotes: NoteDTO[];
  meetingNotes: NoteDTO[];
  followUpNotes: NoteDTO[];
};

/**
 * Fetches notes for a specific jobseeker based on the provided jobseekerId.
 *
 * @param {string} jobseekerId - The ID of the jobseeker for whom notes need to be retrieved.
 * @return {Promise<NoteDTO[]>} - A promise that resolves to an array of NoteDTO objects representing the notes.
 */
export const getCareerPrepStudentNotes = async (
  jobseekerId: string,
): Promise<CategorizedNotes> => {
  const notes = await prisma.caseMgmtNotes.findMany({
    where: {
      jobseekerId: jobseekerId,
    },
    select: {
      id: true,
      jobseekerId: true,
      createdBy: true,
      noteType: true,
      noteContent: true,
      createdAt: true,
      updatedAt: true,
      date: true,
      Author: {
        select: {
          first_name: true,
          last_name: true,
        },
      },
    },
    orderBy: {
      createdAt: "desc",
    },
  });

  // Map notes to NoteDTO
  const flattenedNotes: NoteDTO[] = notes.map((note) => ({
    id: note.id,
    jobseekerId: note.jobseekerId,
    createdBy: note.createdBy,
    noteType: note.noteType as NoteType,
    noteContent: note.noteContent,
    createdAt: note.createdAt.toISOString(),
    updatedAt: note.updatedAt.toISOString(),
    date: note.date ? note.date.toISOString() : null,
    authorName:
      `${note.Author?.first_name || ""} ${note.Author?.last_name || ""}`.trim(),
  }));

  const sortedNotes: CategorizedNotes = {
    generalNotes: flattenedNotes.filter(
      (note) => note.noteType === NoteType.GENERAL,
    ),
    meetingNotes: flattenedNotes.filter(
      (note) => note.noteType === NoteType.MEETING,
    ),
    followUpNotes: flattenedNotes.filter(
      (note) => note.noteType === NoteType.FOLLOWUP,
    ),
  };
  return sortedNotes;
};

export const addCareerPrepStudentNotes = async (
  jobseekerId: string,
  noteContent: string,
  noteType: string,
  updatedDate: Date,
) => {
  const Session = await auth();
  try {
    if (Session?.user.id == undefined || Session.user.id == null) {
      throw new Error("id was null or undefinded");
    }

    const result = await prisma.caseMgmtNotes.create({
      data: {
        jobseekerId: jobseekerId,
        date: updatedDate,
        noteType: noteType,
        noteContent: noteContent,
        createdBy: Session.user.id,
        updatedAt: updatedDate,
      },
    });
    return result;
  } catch (e) {
    console.error(e);
  }
};

export async function updateCareerPrepStudentNotes(
  noteId: string,
  noteContent: string,
  noteType: string,
  updatedDate: Date,
) {
  const Session = await auth();
  try {
    if (Session?.user.id == undefined || Session.user.id == null) {
      throw new Error("id was null or undefinded");
    }
    const result = await prisma.caseMgmtNotes.update({
      where: {
        id: noteId,
      },
      data: {
        noteContent: noteContent,
        noteType: noteType,
        updatedAt: updatedDate,
      },
    });
    return result;
  } catch (e) {
    console.error(e);
  }
}

export async function deleteCareerPrepStudentNotes(noteId: string) {
  const result = await prisma.caseMgmtNotes.delete({
    where: {
      id: noteId,
    },
  });
  return result;
}

/**
 * Represents the different types of notes that can be associated with a task or event.
 * @enum {string}
 */
export enum NoteType {
  GENERAL = "General", // for general purpose
  MEETING = "Meeting", // associated with meetings
  FOLLOWUP = "Follow-up", // communication notes
}

/**
 * Represents a data transfer object for Career Prep Skills Assessment information.
 */
export type CareerPrepSkillsAssessmentDTO = {
  jobseekerId: string; // Unique identifier for the user completing the form
  basicInformation: {
    pronouns: string;
    expectedEduCompletion: TimeUntilCompletion; // how many months until completing education program
  };
  workExperienceAndMaterials: {
    hasWorkExperience: boolean; // technical or non-technical work experience
    hasResume: boolean; // will use getResumeUrl(userId) to confirm
    // resumeLink?: string; // open link with getResumeUrl(userId)
    hasPortfolio: boolean; // check jobseekers.portfolioUrl
    portfolioLink?: string; // Optional, only if 'hasPortfolio' is true
    hasCoverLetter: boolean; // will use getCoverLetter(userId) to confirm
    // coverLetterLink?: string; // open link with getCoverLetter(userId)
    hasLinkedInProfile: boolean; // check jobseekers.linkedInUrl
    linkedInLink?: string; // use value in jobseekers.linkedInUrl
    experienceWithApplying: boolean;
    experienceWithInterviewing: boolean;
  };
  technicalSelfAssessment: {
    interestPathway: CareerPrepPathways;
    skillRatings: {
      cybersecurity?: CybersecuritySkills;
      dataAnalytics?: DataAnalyticsSkills;
      itAndCloudComputing?: ItAndCloudSupportSkills;
      softwareDevelopment?: SoftwareDeveloperSkills;
    };
  };
  durableSkills: DurableSkillsRatings;
  professionalBrandingAndJobMarketReadiness: ProfessionalBrandingRatings;
};

/**
 * Represents a data transfer object for Career Prep Enrollment information.
 */
export type CareerPrepEnrollmentDTO = {
  streetAddress: string;
  priorityPopulations: string;
};

/**
 * Submits a career preparation skills assessment with session data.
 *
 * @param {CareerPrepSkillsAssessmentDTO} data - The data of career preparation skills assessment to be submitted.
 */
export const submitCareerPrepAssessmentWithSession = async (
  data: CareerPrepSkillsAssessmentDTO,
): Promise<{ success: boolean; status: number } | null> => {
  const session = await auth();
  const jobseekerId = session?.user.jobseekerId;
  if (!jobseekerId) {
    console.error("No jobseeker id was provided from session data...");
    return null;
  }
  devLog("DTO", data);
  await submitCareerPrepAssessment(jobseekerId, data);
  return { success: true, status: 200 };
};
export const submitCareerPrepAssessment = async (
  jobseekerId: string,
  data: CareerPrepSkillsAssessmentDTO,
): Promise<{ success: boolean; status: number } | null> => {
  try {
    const result = await prisma.$transaction(
      async (prisma) => {
        await upsertCareerPrepAssessment(prisma, jobseekerId, data);

        await upsertDurableSkillRatings(
          prisma,
          jobseekerId,
          data.durableSkills,
        );

        await upsertBrandRatings(
          prisma,
          jobseekerId,
          data.professionalBrandingAndJobMarketReadiness,
        );

        await upsertPathwayRatings(
          prisma,
          jobseekerId,
          data.technicalSelfAssessment,
        );

        // //TODO: determine case manager with least amount of assigned jobseekers
        await upsertUnassignedCaseMgmtRecord(prisma, jobseekerId);

        return { success: true, status: 200 };
      },
      {
        timeout: 10000, // Timeout in milliseconds (e.g., 10000 ms = 10 seconds)
      },
    );
    devLog("result", result);
    return { success: true, status: 200 };
  } catch (e: any) {
    console.error("Failed to submit Career Prep Assessment records", e.message);
    return { success: false, status: 500 };
  }
};
/**
 *
 * @param jobseekerId
 * @returns
 */
export const getCareerPrepAssessment = async (jobseekerId: string) => {
  //todo: add find on careerPrepAssessment
  try {
    const result = await prisma.careerPrepAssessment.findUnique({
      where: { jobseekerId: jobseekerId },
      include: {
        CybersecurityRating: true,
        DataAnalyticsRating: true,
        ITCloudRating: true,
        SoftwareDevRating: true,
        DurableSkillsRating: true,
        BrandingRating: true,
      },
    });
    return result;
  } catch (error) {
    console.error(error);
  }
};

export type CareerPrepApplicationDTO = Record<string, string>;

/**
 * Submits a Career Prep application to the Microsoft List endpoint.
 *
 * @param {CareerPrepApplicationDTO} data - Flattened payload representing the application form.
 * @returns {Promise<{ success: boolean; status: number; data?: any; error?: string }>}
 */
export const submitCareerPrepApplication = async (
  data: CareerPrepApplicationDTO,
): Promise<{
  success: boolean;
  status: number;
  data?: any;
  error?: string;
}> => {
  const endpoint = process.env.CP_APPLICATION_ENDPOINT;
  if (!endpoint) {
    return { success: false, status: 500, error: "Server not configured" };
  }

  try {
    const resp = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
      signal: AbortSignal.timeout(15_000),
    });

    const raw = await resp.text().catch(() => "");
    let parsed: any = null;
    try {
      parsed = raw ? JSON.parse(raw) : null;
    } catch {}

    if (!resp.ok) {
      return {
        success: false,
        status: resp.status || 502,
        error: (raw || "Upstream failed").slice(0, 500),
      };
    }

    return { success: true, status: resp.status || 200, data: parsed ?? raw };
  } catch (e: any) {
    return {
      success: false,
      status: 500,
      error: e?.message ?? "Unknown error",
    };
  }
};

/**
 * Submits a career preparation skills assessment with session data.
 *
 * @param {CareerPrepEnrollmentDTO} data - The data of career preparation skills assessment to be submitted.
 */
export const submitCareerPrepEnrollment = async (
  data: CareerPrepEnrollmentDTO,
): Promise<{ success: boolean; status: number } | null> => {
  const session = await auth();
  const jobseekerId = session?.user.jobseekerId;
  if (!jobseekerId) {
    console.error("No jobseeker id was provided from session data...");
    return null;
  }
  devLog("DTO", data);
  try {
    const result = await prisma.$transaction(
      async (tx) => {
        await updateCareerPrepEnrollment(tx, jobseekerId, data);
        await updateCareerPrepStatusCardViewTx(
          tx,
          jobseekerId,
          CareerPrepStatus.Enrolled,
        );
        return { success: true, status: 200 };
      },
      {
        timeout: 10000, // Timeout in milliseconds (e.g., 10000 ms = 10 seconds)
      },
    );
    devLog("result", result);
    return { success: true, status: 200 };
  } catch (e: any) {
    console.error("Failed to submit Career Prep Enrollment records", e.message);
    return { success: false, status: 500 };
  }
};

/**
 * Asynchronously upserts a case management record for a specific jobseeker.
 *
 * @param {string} jobseekerId - The ID of the jobseeker for whom the case management record will be upserted.
 * @returns {Promise<{ success: boolean, status: number }>} A promise that resolves with an object indicating the success and status of the upsert operation.
 */
const upsertUnassignedCaseMgmtRecord = async (
  prisma: TransactionClient,
  jobseekerId: string,
): Promise<{ success: boolean; status: number }> => {
  try {
    //get necessary info from jobseeker table
    const jobseeker = await prisma.jobseekers.findUnique({
      where: {
        jobseeker_id: jobseekerId,
      },
    });

    await prisma.caseMgmt.upsert({
      where: {
        jobseekerId,
      },
      update: {
        PrepAssessment: {
          connect: {
            jobseekerId,
          },
        },
      },
      create: {
        prepEnrollmentStatus: CareerPrepStatus.Applied,
        careerPrepTrack: jobseeker?.careerPrepTrackRecommendation || null,
        PrepAssessment: {
          connect: {
            jobseekerId,
          },
        },
      },
    });
    return { success: true, status: 200 };
  } catch (e) {
    console.error("Failed to upsert Case Management record", e);
    return { success: false, status: 500 };
  }
};

/**
 * Upsert Professional Brand Ratings for a specific jobseeker.
 * @param {string} jobseekerId - The ID of the jobseeker to update ratings for.
 * @param {ProfessionalBrandingRatings} brand - The Professional Brand Ratings to upsert.
 * @returns {Promise<ProfessionalBrandingRatings | null>} - The updated Professional Brand Ratings or null if failed.
 */
const upsertBrandRatings = async (
  prisma: TransactionClient,
  jobseekerId: string,
  brand: ProfessionalBrandingRatings,
): Promise<{
  success: boolean;
  status: number;
}> => {
  try {
    await prisma.brandingRating.upsert({
      where: {
        jobseekerId,
      },
      update: {
        personalBrand: brand.personalBrand,
        onlinePresence: brand.onlinePresence,
        elevatorPitch: brand.elevatorPitch,
        resumeEffectiveness: brand.resumeEffectiveness,
        coverLetterEffectiveness: brand.coverLetterEffectiveness,
        interviewExperience: brand.interviewExperience,
        responseTechnique: brand.responseTechnique,
        followUpImportance: brand.followUpImportance,
        onlineNetworking: brand.onlineNetworking,
        eventNetworking: brand.eventNetworking,
        relationshipManagement: brand.relationshipManagement,
        jobSearchStrategy: brand.jobSearchStrategy,
        materialDistribution: brand.materialDistribution,
        networkingTechniques: brand.networkingTechniques,
        onboardingBestPractices: brand.onboardingBestPractices,
        developmentPlan: brand.developmentPlan,
        mentorship: brand.mentorship,
      },
      create: {
        personalBrand: brand.personalBrand,
        onlinePresence: brand.onlinePresence,
        elevatorPitch: brand.elevatorPitch,
        resumeEffectiveness: brand.resumeEffectiveness,
        coverLetterEffectiveness: brand.coverLetterEffectiveness,
        interviewExperience: brand.interviewExperience,
        responseTechnique: brand.responseTechnique,
        followUpImportance: brand.followUpImportance,
        onlineNetworking: brand.onlineNetworking,
        eventNetworking: brand.eventNetworking,
        relationshipManagement: brand.relationshipManagement,
        jobSearchStrategy: brand.jobSearchStrategy,
        materialDistribution: brand.materialDistribution,
        networkingTechniques: brand.networkingTechniques,
        onboardingBestPractices: brand.onboardingBestPractices,
        developmentPlan: brand.developmentPlan,
        mentorship: brand.mentorship,
        PrepAssessment: {
          connect: {
            jobseekerId,
          },
        },
      },
    });
    return { success: true, status: 200 };
  } catch (e) {
    console.error("Failed to submit Professional Brand Ratings", e);
    return { success: false, status: 500 };
  }
};

const upsertCareerPrepAssessment = async (
  prisma: TransactionClient,
  jobseekerId: string,
  data: CareerPrepSkillsAssessmentDTO,
): Promise<{ success: boolean; status: number }> => {
  await prisma.careerPrepAssessment.upsert({
    where: {
      jobseekerId: data.jobseekerId,
    },
    update: {
      pronouns: data.basicInformation.pronouns,
      expectedEduCompletion: data.basicInformation.expectedEduCompletion,
      experienceWithApplying:
        data.workExperienceAndMaterials.experienceWithApplying,
      experienceWithInterview:
        data.workExperienceAndMaterials.experienceWithInterviewing,
      prevWorkExperience: data.workExperienceAndMaterials.hasWorkExperience,
      interestPathway: data.technicalSelfAssessment.interestPathway,
    },
    create: {
      pronouns: data.basicInformation.pronouns,
      expectedEduCompletion: data.basicInformation.expectedEduCompletion,
      experienceWithApplying:
        data.workExperienceAndMaterials.experienceWithApplying,
      experienceWithInterview:
        data.workExperienceAndMaterials.experienceWithInterviewing,
      prevWorkExperience: data.workExperienceAndMaterials.hasWorkExperience,
      interestPathway: data.technicalSelfAssessment.interestPathway,
      Jobseeker: {
        connect: {
          jobseeker_id: jobseekerId,
        },
      },
    },
  });

  return { success: true, status: 200 };
};

/**
 * Upsert durable skill ratings for a specific jobseeker.
 *
 * @param {string} jobseekerId - The ID of the jobseeker for whom the durable skill ratings are being upserted.
 * @param {CareerPrepSkillsAssessmentDTO['durableSkills']} softSkills - The durable skills ratings to be updated or created.
 *
 * @returns {Promise<DurableSkillsRatings | null>} - The updated durable skills ratings or null if an error occurs.
 */
const upsertDurableSkillRatings = async (
  prisma: TransactionClient,
  jobseekerId: string,
  softSkills: CareerPrepSkillsAssessmentDTO["durableSkills"],
): Promise<{ success: boolean; status: number }> => {
  try {
    await prisma.durableSkillsRating.upsert({
      where: {
        jobseekerId,
      },
      update: {
        emotionManagement: softSkills.emotionManagement,
        empathy: softSkills.empathy,
        goalSetting: softSkills.goalSetting,
        timeManagement: softSkills.timeManagement,
        adaptability: softSkills.adaptability,
        criticalThinking: softSkills.criticalThinking,
        creativity: softSkills.creativity,
        resilience: softSkills.resilience,
        communication: softSkills.communication,
        activeListening: softSkills.activeListening,
        conflictResolution: softSkills.conflictResolution,
        nonverbalCommunication: softSkills.nonverbalCommunication,
        teamwork: softSkills.teamwork,
        trustBuilding: softSkills.trustBuilding,
        leadership: softSkills.leadership,
        perspectiveTaking: softSkills.perspectiveTaking,
        culturalAwareness: softSkills.culturalAwareness,
        relationshipBuilding: softSkills.relationshipBuilding,
        documentationSkills: softSkills.documentationSkills,
      },
      create: {
        emotionManagement: softSkills.emotionManagement,
        empathy: softSkills.empathy,
        goalSetting: softSkills.goalSetting,
        timeManagement: softSkills.timeManagement,
        adaptability: softSkills.adaptability,
        criticalThinking: softSkills.criticalThinking,
        creativity: softSkills.creativity,
        resilience: softSkills.resilience,
        communication: softSkills.communication,
        activeListening: softSkills.activeListening,
        conflictResolution: softSkills.conflictResolution,
        nonverbalCommunication: softSkills.nonverbalCommunication,
        teamwork: softSkills.teamwork,
        trustBuilding: softSkills.trustBuilding,
        leadership: softSkills.leadership,
        perspectiveTaking: softSkills.perspectiveTaking,
        culturalAwareness: softSkills.culturalAwareness,
        relationshipBuilding: softSkills.relationshipBuilding,
        documentationSkills: softSkills.documentationSkills,
        PrepAssessment: {
          connect: {
            jobseekerId,
          },
        },
      },
    });
    return { success: true, status: 200 };
  } catch (e) {
    console.error("Error in upsertDurableSkills:", e);
    return { success: false, status: 500 };
  }
};

/**
 * Upsert pathway skills for a jobseeker based on their technical self-assessment.
 * @param {string} jobseekerId - The ID of the jobseeker
 * @param {CareerPrepSkillsAssessmentDTO["technicalSelfAssessment"]} techAssessment - The technical self-assessment data
 */
const upsertPathwayRatings = async (
  prisma: TransactionClient,
  jobseekerId: string,
  techAssessment: CareerPrepSkillsAssessmentDTO["technicalSelfAssessment"],
): Promise<{ success: boolean; status: number }> => {
  switch (techAssessment.interestPathway) {
    case CareerPrepPathways.DATA_ANALYTICS:
      await prisma.dataAnalyticsRating.upsert({
        where: { jobseekerId },
        update: {
          ...techAssessment.skillRatings?.dataAnalytics,
        },
        create: {
          ...techAssessment.skillRatings?.dataAnalytics!,
          PrepAssessment: {
            connect: {
              jobseekerId,
            },
          },
        },
      });
      break;

    case CareerPrepPathways.CYBERSECURITY:
      await prisma.cybersecurityRating.upsert({
        where: { jobseekerId },
        update: {
          ...techAssessment.skillRatings?.cybersecurity,
        },
        create: {
          ...techAssessment.skillRatings?.cybersecurity!,
          PrepAssessment: {
            connect: {
              jobseekerId,
            },
          },
        },
      });
      break;

    case CareerPrepPathways.IT_CLOUD_SUPPORT:
      await prisma.iTCloudRating.upsert({
        where: { jobseekerId },
        update: {
          ...techAssessment.skillRatings.itAndCloudComputing,
        },
        create: {
          ...techAssessment.skillRatings.itAndCloudComputing!,

          PrepAssessment: {
            connect: {
              jobseekerId,
            },
          },
        },
      });
      break;

    case CareerPrepPathways.SOFTWARE_DEVELOPER:
      await prisma.softwareDevRating.upsert({
        where: { jobseekerId },
        update: {
          ...techAssessment.skillRatings?.softwareDevelopment,
          // softwareEngineering:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareEngineering,
          // softwareDevelopmentLifecycle:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareDevelopmentLifecycle,
          // programmingLanguages:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.programmingLanguages,
          // dataStructuresAndAlgorithms:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.dataStructuresAndAlgorithms,
          // softwareArchitecture:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareArchitecture,
          // versionControl:
          //   techAssessment.skillRatings?.softwareDevelopment?.versionControl,
          // databaseManagement:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.databaseManagement,
          // devOps: techAssessment.skillRatings?.softwareDevelopment?.devOps,
          // cloudComputing:
          //   techAssessment.skillRatings?.softwareDevelopment?.cloudComputing,
          // conceptualSystemsThinking:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.conceptualSystemsThinking,
          // problemSolving:
          //   techAssessment.skillRatings?.softwareDevelopment?.problemSolving,
          // fundamentalCodingConcepts:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.fundamentalCodingConcepts,
          // debugging:
          //   techAssessment.skillRatings?.softwareDevelopment?.debugging,
          // computationalThinking:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.computationalThinking,
          // softwareOptimization:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareOptimization,
        },
        create: {
          ...techAssessment.skillRatings?.softwareDevelopment!,
          // softwareEngineering:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareEngineering!,
          // softwareDevelopmentLifecycle:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareDevelopmentLifecycle!,
          // programmingLanguages:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.programmingLanguages!,
          // dataStructuresAndAlgorithms:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.dataStructuresAndAlgorithms!,
          // softwareArchitecture:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareArchitecture!,
          // versionControl:
          //   techAssessment.skillRatings?.softwareDevelopment?.versionControl!,
          // databaseManagement:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.databaseManagement!,
          // devOps: techAssessment.skillRatings?.softwareDevelopment?.devOps!,
          // cloudComputing:
          //   techAssessment.skillRatings?.softwareDevelopment?.cloudComputing!,
          // conceptualSystemsThinking:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.conceptualSystemsThinking!,
          // problemSolving:
          //   techAssessment.skillRatings?.softwareDevelopment?.problemSolving!,
          // fundamentalCodingConcepts:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.fundamentalCodingConcepts!,
          // debugging:
          //   techAssessment.skillRatings?.softwareDevelopment?.debugging!,
          // computationalThinking:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.computationalThinking!,
          // softwareOptimization:
          //   techAssessment.skillRatings?.softwareDevelopment
          //     ?.softwareOptimization!,
          PrepAssessment: {
            connect: {
              jobseekerId,
            },
          },
        },
      });
      break;

    default:
      throw new Error(`Unsupported pathway: ${techAssessment.interestPathway}`);
  }
  return { success: true, status: 200 };
};

/**
 * Upsert career prep enrollment for a specific jobseeker.
 *
 * @param {string} jobseekerId - The ID of the jobseeker for whom the career prep enrollment are being upserted.
 * @param {CareerPrepEnrollmentDTO} softSkills - The enrollment fields to be updated or created.
 *
 * @returns {Promise<CareerPrepEnrollmentDTO | null>} - The updated enrollment fields or null if an error occurs.
 */
const updateCareerPrepEnrollment = async (
  prisma: TransactionClient,
  jobseekerId: string,
  enrollment: CareerPrepEnrollmentDTO,
): Promise<{ success: boolean; status: number }> => {
  try {
    await prisma.careerPrepAssessment.update({
      where: {
        jobseekerId,
      },
      data: {
        streetAddress: enrollment.streetAddress,
        priorityPopulations: enrollment.priorityPopulations,
      },
    });

    return { success: true, status: 200 };
  } catch (e) {
    console.error("Error in upsertDurableSkills:", e);
    return { success: false, status: 500 };
  }
};

/**
 * Retrieves the technology ratings for a specific jobseeker based on the targeted pathway.
 * @param {string} jobseekerId - The ID of the jobseeker.
 * @param {CareerPrepPathways} targetedPathway - The targeted technology pathway.
 * @returns {Promise<CybersecuritySkills | DataAnalyticsSkills | ItAndCloudSupportSkills | SoftwareDeveloperSkills | null>} - The technology ratings based on the pathway.
 */
export const getTechRatings = async (
  jobseekerId: string,
  targetedPathway: CareerPrepPathways,
): Promise<
  | CybersecuritySkills
  | DataAnalyticsSkills
  | ItAndCloudSupportSkills
  | SoftwareDeveloperSkills
  | null
> => {
  switch (targetedPathway) {
    case CareerPrepPathways.CYBERSECURITY:
      const cybersecurityData = await prisma.cybersecurityRating.findUnique({
        where: { jobseekerId },
      });
      return cybersecurityData
        ? {
            overallAverage: cybersecurityData.overallAverage,
            networking: cybersecurityData.networking,
            projectManagement: cybersecurityData.projectManagement,
            securityTools: cybersecurityData.securityTools,
            operatingSystems: cybersecurityData.operatingSystems,
            programming: cybersecurityData.programming,
            cryptography: cybersecurityData.cryptography,
            cloudSecurity: cybersecurityData.cloudSecurity,
            incidentResponse: cybersecurityData.incidentResponse,
            dataSecurity: cybersecurityData.dataSecurity,
            technicalSupport: cybersecurityData.technicalSupport,
            computationalThinking: cybersecurityData.computationalThinking,
            apiUsage: cybersecurityData.apiUsage,
          }
        : null;

    case CareerPrepPathways.DATA_ANALYTICS:
      const dataAnalyticsData = await prisma.dataAnalyticsRating.findUnique({
        where: { jobseekerId },
      });
      return dataAnalyticsData
        ? {
            overallAverage: dataAnalyticsData.overallAverage,
            dataAnalysis: dataAnalyticsData.dataAnalysis,
            sqlProgramming: dataAnalyticsData.sqlProgramming,
            pythonPackages: dataAnalyticsData.pythonPackages,
            dataScience: dataAnalyticsData.dataScience,
            dataEngineering: dataAnalyticsData.dataEngineering,
            tableau: dataAnalyticsData.tableau,
            machineLearning: dataAnalyticsData.machineLearning,
            rProgramming: dataAnalyticsData.rProgramming,
            projectManagement: dataAnalyticsData.projectManagement,
            dataVisualization: dataAnalyticsData.dataVisualization,
            dataStructures: dataAnalyticsData.dataStructures,
            bigOComplexity: dataAnalyticsData.bigOComplexity,
            sortingAlgorithms: dataAnalyticsData.sortingAlgorithms,
            databases: dataAnalyticsData.databases,
            computationalThinking: dataAnalyticsData.computationalThinking,
          }
        : null;

    case CareerPrepPathways.IT_CLOUD_SUPPORT:
      const itCloudData = await prisma.iTCloudRating.findUnique({
        where: { jobseekerId },
      });
      return itCloudData
        ? {
            overallAverage: itCloudData.overallAverage,
            techSupport: itCloudData.techSupport,
            activeDirectory: itCloudData.activeDirectory,
            projectManagement: itCloudData.projectManagement,
            helpDeskSupport: itCloudData.helpDeskSupport,
            windowsServers: itCloudData.windowsServers,
            sqlProgramming: itCloudData.sqlProgramming,
            computerHardware: itCloudData.computerHardware,
            operatingSystems: itCloudData.operatingSystems,
            systemAdmin: itCloudData.systemAdmin,
            networkAdmin: itCloudData.networkAdmin,
            virtualization: itCloudData.virtualization,
            coreCloudServices: itCloudData.coreCloudServices,
            apiUsage: itCloudData.apiUsage,
            httpResponseCodes: itCloudData.httpResponseCodes,
            computationalThinking: itCloudData.computationalThinking,
          }
        : null;

    case CareerPrepPathways.SOFTWARE_DEVELOPER:
      const softwareDevData = await prisma.softwareDevRating.findUnique({
        where: { jobseekerId },
      });
      return softwareDevData
        ? {
            overallAverage: softwareDevData.overallAverage,
            softwareEngineering: softwareDevData.softwareEngineering,
            softwareDevelopmentLifecycle:
              softwareDevData.softwareDevelopmentLifecycle,
            programmingLanguages: softwareDevData.programmingLanguages,
            dataStructuresAndAlgorithms:
              softwareDevData.dataStructuresAndAlgorithms,
            softwareArchitecture: softwareDevData.softwareArchitecture,
            versionControl: softwareDevData.versionControl,
            databaseManagement: softwareDevData.databaseManagement,
            devOps: softwareDevData.devOps,
            cloudComputing: softwareDevData.cloudComputing,
            conceptualSystemsThinking:
              softwareDevData.conceptualSystemsThinking,
            problemSolving: softwareDevData.problemSolving,
            fundamentalCodingConcepts:
              softwareDevData.fundamentalCodingConcepts,
            debugging: softwareDevData.debugging,
            computationalThinking: softwareDevData.computationalThinking,
            softwareOptimization: softwareDevData.softwareOptimization,
          }
        : null;

    default:
      throw new Error(`Unknown pathway: ${targetedPathway}`);
  }
};

/**
 * Retrieves durable skills ratings for a specific jobseeker.
 *
 * @param {string} jobseekerId - The unique identifier of the jobseeker.
 * @returns {Promise<DurableSkillsRatings | null>} - A promise that resolves with the durable skills ratings
 * object if found, or null if no data is found for the jobseeker.
 */
export const getDurableSkillRatings = async (
  jobseekerId: string,
): Promise<DurableSkillsRatings | null> => {
  const durableSkillsData = await prisma.durableSkillsRating.findUnique({
    where: {
      jobseekerId,
    },
  });

  return durableSkillsData
    ? {
        overallAverage: durableSkillsData.overallAverage,
        emotionManagement: durableSkillsData.emotionManagement,
        empathy: durableSkillsData.empathy,
        goalSetting: durableSkillsData.goalSetting,
        timeManagement: durableSkillsData.timeManagement,
        adaptability: durableSkillsData.adaptability,
        criticalThinking: durableSkillsData.criticalThinking,
        creativity: durableSkillsData.creativity,
        resilience: durableSkillsData.resilience,
        communication: durableSkillsData.communication,
        activeListening: durableSkillsData.activeListening,
        conflictResolution: durableSkillsData.conflictResolution,
        nonverbalCommunication: durableSkillsData.nonverbalCommunication,
        teamwork: durableSkillsData.teamwork,
        trustBuilding: durableSkillsData.trustBuilding,
        leadership: durableSkillsData.leadership,
        perspectiveTaking: durableSkillsData.perspectiveTaking,
        culturalAwareness: durableSkillsData.culturalAwareness,
        relationshipBuilding: durableSkillsData.relationshipBuilding,
        documentationSkills: durableSkillsData.documentationSkills,
      }
    : null;
};

/**
 * Asynchronously retrieves the branding ratings of a jobseeker.
 *
 * @param {string} jobseekerId - The ID of the jobseeker for whom branding ratings are requested.
 * @returns {Promise<ProfessionalBrandingRatings | null>} A promise that resolves to the branding ratings of the jobseeker if found, otherwise null.
 */
export const getBrandingRatings = async (
  jobseekerId: string,
): Promise<ProfessionalBrandingRatings | null> => {
  const brandingData = await prisma.brandingRating.findUnique({
    where: {
      jobseekerId,
    },
  });

  return brandingData
    ? {
        overallAverage: brandingData.overallAverage,
        personalBrand: brandingData.personalBrand,
        onlinePresence: brandingData.onlinePresence,
        elevatorPitch: brandingData.elevatorPitch,
        resumeEffectiveness: brandingData.resumeEffectiveness,
        coverLetterEffectiveness: brandingData.coverLetterEffectiveness,
        interviewExperience: brandingData.interviewExperience,
        responseTechnique: brandingData.responseTechnique,
        followUpImportance: brandingData.followUpImportance,
        onlineNetworking: brandingData.onlineNetworking,
        eventNetworking: brandingData.eventNetworking,
        relationshipManagement: brandingData.relationshipManagement,
        jobSearchStrategy: brandingData.jobSearchStrategy,
        materialDistribution: brandingData.materialDistribution,
        networkingTechniques: brandingData.networkingTechniques,
        onboardingBestPractices: brandingData.onboardingBestPractices,
        developmentPlan: brandingData.developmentPlan,
        mentorship: brandingData.mentorship,
      }
    : null;
};
// TODO: Align with ICT Job Group Families
// Career Prep Pathways are a subset of enum EduProviderPathways
export enum CareerPrepPathways {
  SOFTWARE_DEVELOPER = "Software Development",
  IT_CLOUD_SUPPORT = "Infrastructure and Operations",
  CYBERSECURITY = "Cybersecurity",
  DATA_ANALYTICS = "Data Science",
  BUSINESS_MGMT = "Business and Management",
  UI_UX_DESIGN = "Design and User Experience",
  TESTING_QUALITY_ASSURANCE = "Testing and Quality Assurance",
}

// Define specific DTOs for skill categories
export type CybersecuritySkills = {
  overallAverage?: number | null;
  networking: SkillProficiency;
  projectManagement: SkillProficiency;
  securityTools: SkillProficiency;
  operatingSystems: SkillProficiency;
  programming: SkillProficiency;
  cryptography: SkillProficiency;
  cloudSecurity: SkillProficiency;
  incidentResponse: SkillProficiency;
  dataSecurity: SkillProficiency;
  technicalSupport: SkillProficiency;
  computationalThinking: SkillProficiency;
  apiUsage: SkillProficiency;
};

export type DataAnalyticsSkills = {
  overallAverage?: number | null;
  dataAnalysis: SkillProficiency;
  sqlProgramming: SkillProficiency;
  pythonPackages: SkillProficiency;
  dataScience: SkillProficiency;
  dataEngineering: SkillProficiency;
  tableau: SkillProficiency;
  machineLearning: SkillProficiency;
  rProgramming: SkillProficiency;
  projectManagement: SkillProficiency;
  dataVisualization: SkillProficiency;
  dataStructures: SkillProficiency;
  bigOComplexity: SkillProficiency;
  sortingAlgorithms: SkillProficiency;
  databases: SkillProficiency;
  computationalThinking: SkillProficiency;
};

export type ItAndCloudSupportSkills = {
  overallAverage?: number | null;
  techSupport: SkillProficiency;
  activeDirectory: SkillProficiency;
  projectManagement: SkillProficiency;
  helpDeskSupport: SkillProficiency;
  windowsServers: SkillProficiency;
  sqlProgramming: SkillProficiency;
  computerHardware: SkillProficiency;
  operatingSystems: SkillProficiency;
  systemAdmin: SkillProficiency;
  networkAdmin: SkillProficiency;
  virtualization: SkillProficiency;
  coreCloudServices: SkillProficiency;
  apiUsage: SkillProficiency;
  httpResponseCodes: SkillProficiency;
  computationalThinking: SkillProficiency;
};

export type SoftwareDeveloperSkills = {
  overallAverage?: number | null;
  softwareEngineering: SkillProficiency;
  softwareDevelopmentLifecycle: SkillProficiency;
  programmingLanguages: SkillProficiency;
  dataStructuresAndAlgorithms: SkillProficiency;
  softwareArchitecture: SkillProficiency;
  versionControl: SkillProficiency;
  databaseManagement: SkillProficiency;
  devOps: SkillProficiency;
  cloudComputing: SkillProficiency;
  conceptualSystemsThinking: SkillProficiency;
  problemSolving: SkillProficiency;
  fundamentalCodingConcepts: SkillProficiency;
  debugging: SkillProficiency;
  computationalThinking: SkillProficiency;
  softwareOptimization: SkillProficiency;
};

export type DurableSkillsRatings = {
  overallAverage?: number | null;
  emotionManagement: SkillLevel;
  empathy: SkillLevel;
  goalSetting: SkillLevel;
  timeManagement: SkillLevel;
  adaptability: SkillLevel;
  criticalThinking: SkillLevel;
  creativity: SkillLevel;
  resilience: SkillLevel;
  communication: SkillLevel;
  activeListening: SkillLevel;
  conflictResolution: SkillLevel;
  nonverbalCommunication: SkillLevel;
  teamwork: SkillLevel;
  trustBuilding: SkillLevel;
  leadership: SkillLevel;
  perspectiveTaking: SkillLevel;
  culturalAwareness: SkillLevel;
  relationshipBuilding: SkillLevel;
  documentationSkills: SkillLevel;
};

export type ProfessionalBrandingRatings = {
  overallAverage?: number | null;
  personalBrand: AgreementLevel;
  onlinePresence: AgreementLevel;
  elevatorPitch: AgreementLevel;
  resumeEffectiveness: AgreementLevel;
  coverLetterEffectiveness: AgreementLevel;
  interviewExperience: AgreementLevel;
  responseTechnique: AgreementLevel;
  followUpImportance: AgreementLevel;
  onlineNetworking: AgreementLevel;
  eventNetworking: AgreementLevel;
  relationshipManagement: AgreementLevel;
  jobSearchStrategy: AgreementLevel;
  materialDistribution: AgreementLevel;
  networkingTechniques: AgreementLevel;
  onboardingBestPractices: AgreementLevel;
  developmentPlan: AgreementLevel;
  mentorship: AgreementLevel;
};

export function getLabel<T extends number | string>(
  score: T,
  labels: Record<T, string>,
): string {
  return labels[score] || "Unknown";
}

// Enum for agreement levels
export enum AgreementLevel {
  StronglyDisagree = 1,
  Disagree = 2,
  Neutral = 3,
  Agree = 4,
  StronglyAgree = 5,
}

export const AgreementLevelLabels: Record<AgreementLevel, string> = {
  [AgreementLevel.StronglyDisagree]: "Strongly Disagree",
  [AgreementLevel.Disagree]: "Disagree",
  [AgreementLevel.Neutral]: "Neutral",
  [AgreementLevel.Agree]: "Agree",
  [AgreementLevel.StronglyAgree]: "Strongly Agree",
};

// Enum for skill proficiency levels
export enum SkillProficiency {
  NotProficient = 1,
  Novice = 2,
  Beginner = 3,
  Competent = 4,
  Proficient = 5,
}

export const SkillProficiencyLabels: Record<SkillProficiency, string> = {
  [SkillProficiency.NotProficient]: "Not Proficient",
  [SkillProficiency.Novice]: "Novice",
  [SkillProficiency.Beginner]: "Beginner",
  [SkillProficiency.Competent]: "Competent",
  [SkillProficiency.Proficient]: "Proficient",
};

// Enum for durable skill levels
export enum SkillLevel {
  NeedsImprovement = 1,
  Developing = 2,
  Fair = 3,
  Good = 4,
  Exceptional = 5,
}

// Label mapping for user-friendly display
export const SkillLevelLabels: Record<SkillLevel, string> = {
  [SkillLevel.NeedsImprovement]: "Needs Improvement",
  [SkillLevel.Developing]: "Developing",
  [SkillLevel.Fair]: "Fair",
  [SkillLevel.Good]: "Good",
  [SkillLevel.Exceptional]: "Exceptional",
};

export interface CreateMeetingDTO {
  jobseekerId: string;
  meetingTitle: string; // VARCHAR(45)
  meetingAgenda?: string; // TEXT (Rich text functionality. Possibly utilize Quill)
  meetingDatetime: Date; // DATETIME
}

export async function addMeeting(params: CreateMeetingDTO) {
  try {
    console.log("Received params:", params);
    const jobseekerExists = await prisma.caseMgmt.findUnique({
      where: { jobseekerId: params.jobseekerId },
    });
    if (!jobseekerExists) {
      throw new Error(`Jobseeker with ID ${params.jobseekerId} not found`);
    }
    const result = await prisma.meeting.create({
      data: {
        jobseekerId: params.jobseekerId,
        title: params.meetingTitle,
        //meetingAgenda: params.meetingAgenda?? "",
        meetingDate: params.meetingDatetime,
        updatedAt: new Date(),
      },
    });
    return result;
  } catch (error) {
    console.error("Error creating meeting:", error);
  }
}

export async function getMeetingByJobSeeker(jobseekerId: string) {
  if (jobseekerId == "") {
    return [];
  }
  try {
    const result = await prisma.meeting.findMany({
      where: {
        jobseekerId: jobseekerId,
      },
    });
    return result;
  } catch (error) {
    console.error(error);
    return [];
  }
}

export async function updateJobStatus(
  newStatus: JobStatus,
  joinTableId: string,
) {
  try {
    return await prisma.jobseekerJobPosting.update({
      where: {
        id: joinTableId,
      },
      data: {
        jobStatus: newStatus,
      },
    });
  } catch (error) {
    console.error(error);
  }
}
