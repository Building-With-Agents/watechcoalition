import { CareerPrepJobseekerCardViewDTO } from "@/app/lib/admin/careerPrep";
import Link from "next/link";
import EnrollmentStatusDropDown from "./EnrollmentStatusDropDown";
import SelfAssignCaseButton from "./SelfAsignCaseButton";

export default function CareerPrepStudentsCard(
  props: CareerPrepJobseekerCardViewDTO & { showSelfAssign: boolean },
) {
  console.log(props.careerPrepEnrollmentStatus);
  return (
    <div className="w-full rounded-lg border border-2 border-cyan-600 p-2 phone:p-4">
      <h3 className="text-2xl">
        {props.firstName} {props.lastName} ({props.pronouns}){" "}
        {props.showSelfAssign ? (
          <SelfAssignCaseButton jobseekerId={props.jobseekerId} />
        ) : (
          ""
        )}
      </h3>
      <p>
        <b>Assigned Track:</b> {props.assignedCareerPrepTrack}
      </p>
      <p>
        <b>Enrollment Status:</b>{" "}
        <EnrollmentStatusDropDown
          careerPrepEnrollmentStatus={props.careerPrepEnrollmentStatus}
          jobseekerId={props.jobseekerId}
        />
      </p>
      <p>
        <b>Expected End Date:</b>{" "}
        {props.careerPrepExpectedEndDate?.toDateString()}
      </p>
      <Link href={"/career-prep/" + props.jobseekerId} className="LINK">
        View Details
      </Link>
    </div>
  );
}
