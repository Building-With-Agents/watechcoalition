import { EduProviderPathways } from "@/app/lib/eduProviders";
import CareerPage from "@/app/ui/components/career/CareerPage";

export default function Page() {
  return (
    <CareerPage
      title={"Software Developer"}
      subtitle={"Build the future, one line of code at a time"}
      img={"/images/careers/software-developer.jpg"}
      altCareerNames={
        "Application Developer, Application Integration Engineer, Developer, Infrastructure Engineer, Network Engineer, Software Architect, Software Developer, Software Development Engineer, Software Engineer, Systems Engineer"
      }
      avgSalary={"$100K/year"}
      trainingLength={"1 - 2 Years"}
      prepLevel={"Medium"}
      description={
        "Software Developers design, code, and maintain software for web, mobile, and desktop applications. They collaborate with teams, troubleshoot issues, and keep software up-to-date, shaping the digital solutions that people use every day."
      }
      whatYoullDo={
        "Design, code, and maintain software for web, mobile, and desktop platforms"
      }
      skillsYoullNeed={
        "Proficiency in programming languages (e.g., Python, Java, Objective-C), analytical thinking, and teamwork"
      }
      whyItMatters={
        "Your solutions will fuel the digital experiences people rely on every day"
      }
      trainingPrograms={EduProviderPathways.SoftwareDeveloper}
    />
  );
}
