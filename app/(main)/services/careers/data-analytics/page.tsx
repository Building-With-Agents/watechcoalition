import { EduProviderPathways } from "@/app/lib/eduProviders";
import CareerPage from "@/app/ui/components/career/CareerPage";

export default function Page() {
  return (
    <CareerPage
      title={"Data Analytics"}
      subtitle={"Turn complex data into Valuable insights"}
      img={"/images/careers/data-analytics.jpg"}
      altCareerNames={
        "Data Scientist, Business Intelligence (BI) Analyst, Data Specialist, Data Engineer, Quantitative Analyst, Marketing Analyst, Operations Analyst, Financial Analyst, Product Analyst, Data Visualization Specialist, Research Analyst, Insights Analyst, Reporting Analyst, Analytics Consultant, Support Analyst, Big Data Analyst"
      }
      avgSalary={"$100K/year"}
      trainingLength={"1 - 2 Years"}
      prepLevel={"Medium"}
      description={
        "Data Analytics Specialists analyze complex datasets to uncover trends and insights. They help businesses make data-driven decisions by translating metrics into clear, actionable information."
      }
      whatYoullDo={
        "Analyze large datasets, discover trends, and help businesses make data-driven decisions"
      }
      skillsYoullNeed={
        "Proficiency in data tools (Python, SQL), analytical thinking, and attention to detail"
      }
      whyItMatters={
        "Your insights will drive strategic decisions, shaping business success and innovation"
      }
      trainingPrograms={EduProviderPathways.DataAnalytics}
    />
  );
}
