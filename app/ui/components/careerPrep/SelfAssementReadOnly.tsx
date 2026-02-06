"use client";
import {
  BrandingRating,
  CareerPrepAssessment,
  CybersecurityRating,
  DataAnalyticsRating,
  DurableSkillsRating,
  ITCloudRating,
  SoftwareDevRating,
} from "@prisma/client";
//import { getCareerPrepAssessment } from "@/app/lib/admin/careerPrep";
import BasicModal from "./BasicModal";
import LikertRating from "./LikertRating";
import { useEffect, useState } from "react";

export default function SelfAssementReadOnly(params: { id: string }) {
  //const assessment = await getCareerPrepAssessment(params.id);
  const [assessment, setAssessment] = useState<
    | (CareerPrepAssessment & {
        BrandingRating: BrandingRating[];
        CybersecurityRating: CybersecurityRating[];
        DataAnalyticsRating: DataAnalyticsRating[];
        ITCloudRating: ITCloudRating[];
        SoftwareDevRating: SoftwareDevRating[];
        DurableSkillsRating: DurableSkillsRating[];
      })
    | null
  >(null);

  useEffect(() => {
    let isMounted = true; // Prevent state update if unmounted

    const fetchData = async () => {
      try {
        const res = await fetch(
          `/api/admin/career-prep/get-prep-assessment/${params.id}`,
        );
        if (!res.ok) throw new Error("Failed to fetch assessment");

        const data = await res.json();
        if (isMounted) setAssessment(data);
      } catch (error) {
        console.error("Error fetching assessment:", error);
      }
    };

    if (params.id) {
      fetchData();
    }

    return () => {
      isMounted = false; // Cleanup function
    };
  }, [params.id]); // Only re-run when `params.id` changes

  const allEmpty = [
    assessment?.BrandingRating,
    assessment?.CybersecurityRating,
    assessment?.DataAnalyticsRating,
    assessment?.ITCloudRating,
    assessment?.SoftwareDevRating,
  ].every((list) => !list || list.length === 0);
  return (
    <div>
      <h1 className="text-xl font-bold"> Self Assessments Taken</h1>
      <div className="space-y-2">
        {allEmpty ? (
          <p className="text-gray-500">No Assessments Found</p>
        ) : (
          <>
            <AssessmentModal
              list={assessment?.DurableSkillsRating}
              title={"Durable Skills"}
            />
            <AssessmentModal
              list={assessment?.BrandingRating}
              title="Branding Rating"
            />
            <AssessmentModal
              list={assessment?.CybersecurityRating}
              title="Cyber Security"
            />
            <AssessmentModal
              list={assessment?.DataAnalyticsRating}
              title="Data Analytics"
            />
            <AssessmentModal
              list={assessment?.ITCloudRating}
              title="IT Cloud"
            />
            <AssessmentModal
              list={assessment?.SoftwareDevRating}
              title="Software Dev"
            />
          </>
        )}
      </div>
    </div>
  );
}
/*
BrandingRating[], 
    CybersecurityRating:CybersecurityRating[],
    DataAnalyticsRating:DataAnalyticsRating[],
    ITCloudRating:ITCloudRating[],
    SoftwareDevRating:SoftwareDevRating[],
    DurableSkillsRating:DurableSkillsRating[]
*/
export function AssessmentModal({
  list,
}: {
  list:
    | CybersecurityRating[]
    | DataAnalyticsRating[]
    | ITCloudRating[]
    | SoftwareDevRating[]
    | DurableSkillsRating[]
    | BrandingRating[]
    | undefined;
  title: string;
}) {
  return list != undefined && list.length > 0 ? (
    <BasicModal
      buttonText={
        list[0].overallAverage ? list[0].overallAverage.toString() : "?"
      }
    >
      {
        <div className="h-[650px] w-fit flex flex-col flex-wrap">
          {Object.entries(list[0] || {}) // Use first item in array
            .filter(([key, value]) => typeof value === "number") // eslint-disable-line @typescript-eslint/no-unused-vars
            .map(([key, value]) => (
              <div key={key} className="m-2.5">
                <label htmlFor={key} className="capitalize">
                  {key.replace(/([A-Z])/g, " $1")}:
                </label>
                <LikertRating value={value as number} />
              </div>
            ))}
        </div>
      }
    </BasicModal>
  ) : (
    "Not Found"
  );
}
