"use client";
import {
  CareerPrepPathways,
  CybersecuritySkills,
  DataAnalyticsSkills,
  ItAndCloudSupportSkills,
  SkillProficiency,
  SkillProficiencyLabels,
  SoftwareDeveloperSkills,
} from "@/app/lib/admin/careerPrep";
import { devLog } from "@/app/lib/utils";
import PillButton from "@/app/ui/components/PillButton";
import ProgressBarFlat from "@/app/ui/components/ProgressBarFlat";
import { JsCareerPrepPathwaySkillsDTO } from "@/data/dtos/JobSeekerProfileCreationDTOs";
import {
  initialState,
  setPathwaySkills,
} from "@/lib/features/profileCreation/jobseekerSlice";
import { setPageSaved } from "@/lib/features/profileCreation/saveSlice";
import { RootState } from "@/lib/jobseekerStore";
import {
  Container,
  FormControl,
  FormLabel,
  MenuItem,
  Radio,
  Select,
  SelectChangeEvent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import _ from "lodash";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

export default function Page() {
  const router = useRouter();
  const dispatch = useDispatch();
  const { data: session, status } = useSession();
  const pathwaySkillsStoreData = useSelector(
    (state: RootState) => state.jobseeker.pathwaySkills,
  );
  const [localPathwaySkills, setLocalPathwaySkills] = useState(
    pathwaySkillsStoreData,
  );

  const pathwayQuestions: Record<
    CareerPrepPathways,
    { id: string; text: string }[]
  > = {
    [CareerPrepPathways.BUSINESS_MGMT]: [
      {
        id: "businessStrategy",
        text: "Business Strategy: Understanding organizational strategy, competitive analysis, and business models.",
      },
      {
        id: "financialLiteracy",
        text: "Financial Literacy: Basic knowledge of budgeting, forecasting, and financial decision-making.",
      },
      {
        id: "projectManagement",
        text: "Project Management: Applying frameworks like Agile, Scrum, or Waterfall to organize and deliver projects.",
      },
      {
        id: "communication",
        text: "Communication: Developing clear written, verbal, and presentation skills for diverse audiences.",
      },
      {
        id: "leadership",
        text: "Leadership: Motivating, managing, and coaching teams to achieve organizational goals.",
      },
      {
        id: "dataDrivenDecisions",
        text: "Data-Driven Decisions: Using data and KPIs to inform management choices.",
      },
    ],

    [CareerPrepPathways.UI_UX_DESIGN]: [
      {
        id: "uxResearch",
        text: "UX Research: Conducting user interviews, surveys, and usability testing to gather insights.",
      },
      {
        id: "uiDesign",
        text: "UI Design: Creating wireframes, prototypes, and high-fidelity mockups with tools like Figma or Adobe XD.",
      },
      {
        id: "designSystems",
        text: "Design Systems: Applying reusable patterns, components, and accessibility standards.",
      },
      {
        id: "interactionDesign",
        text: "Interaction Design: Designing intuitive interactions and user flows.",
      },
      {
        id: "accessibility",
        text: "Accessibility: Ensuring inclusive design principles (WCAG, ARIA).",
      },
      {
        id: "visualDesign",
        text: "Visual Design: Applying typography, color theory, and layout principles.",
      },
    ],

    [CareerPrepPathways.TESTING_QUALITY_ASSURANCE]: [
      {
        id: "manualTesting",
        text: "Manual Testing: Writing and executing test cases to validate software functionality.",
      },
      {
        id: "automatedTesting",
        text: "Automated Testing: Building and maintaining test scripts with frameworks like Selenium, Jest, or Cypress.",
      },
      {
        id: "qaProcesses",
        text: "QA Processes: Understanding unit, integration, system, and acceptance testing.",
      },
      {
        id: "bugTracking",
        text: "Bug Tracking: Documenting, prioritizing, and resolving issues using tools like JIRA or Azure DevOps.",
      },
      {
        id: "performanceTesting",
        text: "Performance Testing: Assessing load, stress, and scalability of software systems.",
      },
      {
        id: "securityTesting",
        text: "Security Testing: Identifying vulnerabilities through penetration testing and code reviews.",
      },
    ],

    [CareerPrepPathways.CYBERSECURITY]: [
      {
        id: "networking",
        text: "Networking: Understanding of network protocols (TCP/IP, HTTP, DNS), network topologies, and network security concepts (firewalls, intrusion detection systems, VPNs).",
      },
      {
        id: "projectManagement",
        text: "Project Management: Planning, organizing, and executing cybersecurity projects",
      },
      {
        id: "securityTools",
        text: "Security Tools and Technologies: Familiarity with various security tools (e.g., SIEM, EDR, vulnerability scanners, malware analysis tools).",
      },
      {
        id: "operatingSystems",
        text: "Operating Systems: Proficiency in Windows, Linux, and macOS, including system administration, security hardening, and troubleshooting.",
      },
      {
        id: "programming",
        text: "Programming: Knowledge of programming languages like Python, C++, or Java, as well as scripting languages like PowerShell or Bash.",
      },
      {
        id: "cryptography",
        text: "Cryptography: Understanding of encryption algorithms (AES, RSA, etc.), hashing functions (SHA, MD5), and key management.",
      },
      {
        id: "cloudSecurity",
        text: "Cloud Security: Familiarity with cloud security best practices, cloud access security brokers (CASBs), and cloud infrastructure security.",
      },
      {
        id: "incidentResponse",
        text: "Incident Response: Ability to handle security incidents, including identifying threats, containing damage, and implementing corrective measures.",
      },
      {
        id: "dataSecurity",
        text: "Data Security: Understanding of data protection regulations (e.g., GDPR, CCPA), data loss prevention (DLP) measures, and data encryption.",
      },
      {
        id: "technicalSupport",
        text: "Technical Support: Providing assistance to users with cybersecurity-related issues",
      },
      {
        id: "computationalThinking",
        text: "Computational Thinking: Demonstrate computational thinking to break down a problem in smaller components as part of solution design or debugging.",
      },
      {
        id: "apiUsage",
        text: "GET/POST requests: Use a RESTful API to consume and edit data via GET/POST requests.",
      },
    ],
    [CareerPrepPathways.DATA_ANALYTICS]: [
      {
        id: "dataAnalysis",
        text: "Data Analysis: Extracting insights and information from data",
      },
      {
        id: "sqlProgramming",
        text: "SQL (Programming Language): Writing SQL queries to interact with databases",
      },
      {
        id: "pythonPackages",
        text: "Python Packages: Utilizing Python packages like Plotly, Seaborn, Pandas, NumPy, and Scikit-learn for data analysis, visualization, and machine learning.",
      },
      {
        id: "dataScience",
        text: "Data Science: Applying statistical and machine learning techniques to data",
      },
      {
        id: "dataEngineering",
        text: "Data Engineering: Designing and building data pipelines and infrastructure",
      },
      {
        id: "tableau",
        text: "Tableau (Business Intelligence Software): Creating interactive data visualizations",
      },
      {
        id: "machineLearning",
        text: "Machine Learning: Developing and implementing machine learning models",
      },
      {
        id: "rProgramming",
        text: "R (Programming Language): Using R for statistical analysis and data visualization",
      },
      {
        id: "projectManagement",
        text: "Project Management: Planning, organizing, and executing data analytics projects",
      },
      {
        id: "dataVisualization",
        text: "Visualizing Data: Creating interactive dashboards to tell a story for data-driven decision-making. ",
      },
      {
        id: "dataStructures",
        text: "Data Structures: Implement data structures including arrays, stacks, queues, linked lists, trees, graphs, and hash tables. ",
      },
      {
        id: "bigOComplexity",
        text: "Big O: Calculate space and time complexity (big O) for a given program. ",
      },
      {
        id: "sortingAlgorithms",
        text: "Sorting Algorithms: Implement sorting algorithms including selection, bubble, insertion, merge, and shell.",
      },
      {
        id: "databases",
        text: "Relational and Non-relational Databases: Compare usecases between/for a relational and non-relational database.",
      },
      {
        id: "computationalThinking",
        text: "Computational Thinking: Demonstrate computational thinking to break down a problem in smaller components as part of solution design or debugging.",
      },
    ],
    [CareerPrepPathways.IT_CLOUD_SUPPORT]: [
      {
        id: "techSupport",
        text: "Technical Support: Providing assistance to users with hardware, software, and network issues",
      },
      {
        id: "activeDirectory",
        text: "Active Directory: Managing user accounts, groups, and permissions in a Windows domain environment",
      },
      {
        id: "projectManagement",
        text: "Project Management: Planning, organizing, and executing IT projects",
      },
      {
        id: "helpDeskSupport",
        text: "Help Desk Support: Providing first-line technical support to users",
      },
      {
        id: "windowsServers",
        text: "Windows Servers: Administering Windows Server operating systems",
      },
      {
        id: "sqlProgramming",
        text: "SQL (Programming Language): Writing SQL queries to interact with databases",
      },
      {
        id: "computerHardware",
        text: "Computer Hardware: Understanding and troubleshooting computer hardware components",
      },
      {
        id: "operatingSystems",
        text: "Operating Systems: Understanding and troubleshooting various operating systems (e.g., Windows, macOS, Linux)",
      },
      {
        id: "systemAdmin",
        text: "System Administration: Managing and maintaining IT systems and infrastructure",
      },
      {
        id: "networkAdmin",
        text: "Network Administration: Networking skills (e.g., configuring routers, switches, and firewalls)",
      },
      {
        id: "virtualization",
        text: "Virtualization/Cloud Technologies: Managing and deploying virtual environments (e.g., VMware, Hyper-V) and cloud platforms (e.g., AWS, Azure).",
      },
      {
        id: "coreCloudServices",
        text: "Core Cloud Services: Compare different core cloud services and explain how they are used, specifically relating to compute, storage, networking, database, security (IAM).",
      },
      {
        id: "apiUsage",
        text: "GET/POST Requests: Use a RESTful API to consume and edit data via GET/POST requests.",
      },
      {
        id: "httpResponseCodes",
        text: "HTTP Response: Explain the different HTTP response status codes.",
      },
      {
        id: "computationalThinking",
        text: "Computational Thinking: Demonstrate computational thinking to break down a problem in smaller components as part of solution design or debugging.",
      },
    ],
    [CareerPrepPathways.SOFTWARE_DEVELOPER]: [
      {
        id: "softwareEngineering",
        text: "Software Engineering: Applying engineering principles to software development",
      },
      {
        id: "softwareDevelopmentLifecycle",
        text: "Software Development Lifecycle: Understanding of the software development lifecycle, including design, development, testing, and maintenance.",
      },
      {
        id: "programmingLanguages",
        text: "Programming Languages: Using programming languages like Python, Java, C++, JavaScript, and C#",
      },
      {
        id: "dataStructuresAndAlgorithms",
        text: "Data Structures and Algorithms: Understanding of fundamental data structures (arrays, linked lists, stacks, queues, trees, graphs) and algorithms (sorting, searching, dynamic programming).  ",
      },
      {
        id: "softwareArchitecture",
        text: "Software Architecture: Knowledge of design principles and patterns (e.g., MVC, Factory, Singleton) to create scalable, maintainable, and efficient systems.",
      },
      {
        id: "versionControl",
        text: "Version Control: Collaborate with a team using advanced git commands including branch, fetch, rebase, stash, revert, config.",
      },
      {
        id: "databaseManagement",
        text: "Database Management: Understanding of relational databases (SQL) and NoSQL databases.",
      },
      {
        id: "devOps",
        text: "DevOps: Knowledge of DevOps practices for automating software development, testing, and deployment.",
      },
      {
        id: "cloudComputing",
        text: "Cloud Computing: Familiarity with cloud platforms (AWS, Azure, GCP) and their services for software development.",
      },
      {
        id: "conceptualSystemsThinking",
        text: "Conceptual Systems Thinking: Grasping how different components of a system interact and contribute to the overall functionality, enabling effective design and troubleshooting. ",
      },
      {
        id: "problemSolving",
        text: "Problem Solving: Identifying, analyzing, and resolving complex issues in software development, ensuring robust and effective solutions. ",
      },
      {
        id: "fundamentalCodingConcepts",
        text: "Fundamental coding concepts: Data structures, conditionals, loops, variables, functions, and/or object oriented principles.",
      },
      {
        id: "debugging",
        text: "Debugging: Utilize debugger and IDE tools to automate issue resolution and help triangulate root cause. ",
      },
      {
        id: "computationalThinking",
        text: "Computational Thinking: Demonstrate computational thinking to break down a problem in smaller components as part of solution design or debugging.",
      },
      {
        id: "softwareOptimization",
        text: "Software Optimization: Ability to optimize software for performance, speed, and scalability.",
      },
    ],
  };

  useEffect(() => {
    if (session?.user?.id && status === "authenticated") {
      const initializeFormFields = async () => {
        if (_.isEqual(localPathwaySkills, initialState.pathwaySkills)) {
          const { id } = session.user;

          try {
            devLog("fetching fresh");
            const response = await fetch(
              "/api/jobseekers/account/technical-skills/get/" + id,
            );

            if (!response.ok) {
            } else {
              const fetchedData: JsCareerPrepPathwaySkillsDTO = (
                await response.json()
              ).result;
              setLocalPathwaySkills(fetchedData);
              devLog(fetchedData);
            }
          } catch (error) {
            console.error(error);
          }
        } else {
          devLog("fetching from store");
        }
      };
      dispatch(setPageSaved("technical-skills"));
      initializeFormFields();
    }
  }, [session?.user?.id, status]);
  const currentPathway =
    (localPathwaySkills.targetedPathway as CareerPrepPathways) || null;
  const questions = pathwayQuestions[currentPathway] || [];
  const currentSkills =
    currentPathway === CareerPrepPathways.SOFTWARE_DEVELOPER
      ? localPathwaySkills.CareerPrepAssessment.softwareDevelopment
      : currentPathway === CareerPrepPathways.DATA_ANALYTICS
        ? localPathwaySkills.CareerPrepAssessment.dataAnalytics
        : currentPathway === CareerPrepPathways.IT_CLOUD_SUPPORT
          ? localPathwaySkills.CareerPrepAssessment.itAndCloudComputing
          : currentPathway === CareerPrepPathways.CYBERSECURITY
            ? localPathwaySkills.CareerPrepAssessment.cybersecurity
            : null;

  const proficiencyOptions = Object.entries(SkillProficiency)
    .filter(([key]) => isNaN(Number(key))) // Filter out numeric keys
    .map(([label, value]) => ({ label, value }));

  const allQuestionsAnswered =
    questions.length > 0 &&
    currentSkills &&
    (questions.every(
      (question) =>
        currentSkills[question.id as keyof typeof currentSkills] != null,
    ) ??
      false);

  const handlePathwayChange = (event: SelectChangeEvent) => {
    const newPathway = event.target.value as CareerPrepPathways;
    setLocalPathwaySkills((prev) => ({
      ...prev,
      targetedPathway: newPathway,
    }));
  };

  const handleRadioChange = useCallback(
    (skillId: string, proficiency: SkillProficiency) => {
      setLocalPathwaySkills((prev) => {
        if (currentPathway === CareerPrepPathways.SOFTWARE_DEVELOPER) {
          return {
            ...prev,
            CareerPrepAssessment: {
              ...prev.CareerPrepAssessment,
              softwareDevelopment: {
                ...initialState.pathwaySkills.CareerPrepAssessment
                  .softwareDevelopment,
                ...prev.CareerPrepAssessment.softwareDevelopment,
                [skillId]: proficiency,
              } as SoftwareDeveloperSkills,
            },
          };
        } else if (currentPathway === CareerPrepPathways.DATA_ANALYTICS) {
          return {
            ...prev,
            CareerPrepAssessment: {
              ...prev.CareerPrepAssessment,
              dataAnalytics: {
                ...initialState.pathwaySkills.CareerPrepAssessment
                  .dataAnalytics,
                ...prev.CareerPrepAssessment.dataAnalytics,
                [skillId]: proficiency,
              } as DataAnalyticsSkills,
            },
          };
        } else if (currentPathway === CareerPrepPathways.IT_CLOUD_SUPPORT) {
          return {
            ...prev,
            CareerPrepAssessment: {
              ...prev.CareerPrepAssessment,
              itAndCloudComputing: {
                ...initialState.pathwaySkills.CareerPrepAssessment
                  .itAndCloudComputing,
                ...prev.CareerPrepAssessment.itAndCloudComputing,
                [skillId]: proficiency,
              } as ItAndCloudSupportSkills,
            },
          };
        } else if (currentPathway === CareerPrepPathways.CYBERSECURITY) {
          return {
            ...prev,
            CareerPrepAssessment: {
              ...prev.CareerPrepAssessment,
              cybersecurity: {
                ...initialState.pathwaySkills.CareerPrepAssessment
                  .cybersecurity,
                ...prev.CareerPrepAssessment.cybersecurity,
                [skillId]: proficiency,
              } as CybersecuritySkills,
            },
          };
        }
        return prev;
      });
      devLog(
        `Updated ${skillId} to ${proficiency} for pathway ${currentPathway}`,
      );
    },
    [currentPathway],
  );

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!session?.user?.id) {
      console.error("User session is not available.");
      return;
    }
    try {
      const response = await fetch(
        "/api/jobseekers/account/technical-skills/upsert",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(localPathwaySkills),
        },
      );

      if (response.ok) {
        dispatch(setPageSaved("technical-skills"));
        dispatch(setPathwaySkills(localPathwaySkills));
        router.push("/edit-profile/jobseeker/durable-skills");
      }
    } catch {}
  }

  return (
    <Container maxWidth="md">
      <ProgressBarFlat progress={(6 / 9) * 100} />
      <Typography sx={{ mb: 1 }}>Step 6/9</Typography>
      <Typography variant="h3" sx={{ fontWeight: 700 }}>
        Technical Skills Assessment
      </Typography>
      <Typography sx={{ my: 2 }}>
        Remember: Your responses will help us understand your current skills and
        identify areas where you might need support in reaching your career
        goals.
      </Typography>
      <FormControl fullWidth>
        <FormLabel>What technology path most interests you?</FormLabel>
        <Select
          value={currentPathway || ""}
          onChange={handlePathwayChange}
          displayEmpty
          fullWidth
          sx={{ mb: 3 }}
        >
          <MenuItem value="" disabled>
            Select a Technology Pathway
          </MenuItem>
          {Object.values(CareerPrepPathways).map((pathway) => (
            <MenuItem key={pathway} value={pathway}>
              {pathway}
            </MenuItem>
          ))}
        </Select>
      </FormControl>
      <form onSubmit={handleSubmit}>
        <Table stickyHeader sx={{ mb: 5 }}>
          <TableHead>
            <TableRow>
              <TableCell></TableCell>
              {proficiencyOptions.map((option) => (
                <TableCell key={option.value}>
                  {SkillProficiencyLabels[option.value as SkillProficiency]}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {questions.map((question) => (
              <TableRow key={question.id}>
                <TableCell>{question.text}</TableCell>
                {proficiencyOptions.map((option) => (
                  <TableCell key={option.value}>
                    <Radio
                      name={question.id.toString()}
                      value={option.value}
                      checked={
                        currentSkills
                          ? currentSkills[
                              question.id as keyof typeof currentSkills
                            ] === option.value
                          : false
                      }
                      onChange={() =>
                        handleRadioChange(
                          question.id,
                          option.value as SkillProficiency,
                        )
                      }
                    />
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
        <Stack direction="row" sx={{ justifyContent: "space-between", mb: 5 }}>
          <PillButton
            variant="outlined"
            onClick={() => {
              router.push("/edit-profile/jobseeker/work-experience");
            }}
          >
            Previous
          </PillButton>
          <PillButton disabled={!allQuestionsAnswered} type="submit">
            Save and Continue
          </PillButton>
        </Stack>
      </form>
    </Container>
  );
}
