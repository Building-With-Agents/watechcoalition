"use client";
import React, { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Radio,
  RadioGroup,
  FormControl,
  FormControlLabel,
  FormLabel,
  Grid,
  Stepper,
  Step,
  StepLabel,
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  TextField,
  Select,
  MenuItem,
  SelectChangeEvent,
} from "@mui/material";
import { useSession } from "next-auth/react";
import {
  AgreementLevel,
  AgreementLevelLabels,
  CareerPrepSkillsAssessmentDTO,
  SkillLevel,
  SkillLevelLabels,
  SkillProficiencyLabels,
  CareerPrepPathways,
  TimeUntilCompletion,
} from "@/app/lib/admin/careerPrep";
import "@/app/ui/profile-creation.css";
import Confetti from "@/app/ui/components/Confetti";
import PillButton from "@/app/ui/components/PillButton";
import { JSX } from "react/jsx-runtime";

interface EvaluationTableProps {
  questions: {
    id: string;
    text: string;
  }[];
  section: string;
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  labels?: Record<number, string>;
  formData: CareerPrepSkillsAssessmentDTO;
}

const EvaluationTable: React.FC<EvaluationTableProps> = ({
  questions,
  section,
  onChange,
  labels = SkillLevelLabels,
  formData,
}) => {
  const levels = Object.entries(labels).map(([value, label]) => ({
    value: String(value),
    label,
  }));

  useEffect(() => {
    questions.forEach((question) => {
      const currentValue = getCurrentValue(question.id);
      if (!currentValue) {
        handleResponseChange(question.id, "3");
      }
    });
  }, []);

  const handleResponseChange = (questionId: string, value: string): void => {
    const syntheticEvent = {
      target: {
        name: `${section}.${questionId}`,
        value,
      },
    } as React.ChangeEvent<HTMLInputElement>;

    onChange(syntheticEvent);
  };

  const getCurrentValue = (questionId: string): string => {
    const keys = section.split(".");
    let current: any = formData;
    for (const key of keys) {
      if (current[key] === undefined) return "";
      current = current[key];
    }
    return String(current[questionId] || "");
  };

  return (
    <TableContainer>
      <Table aria-label="evaluation table">
        <TableHead>
          <TableRow>
            <TableCell sx={{ width: "30%" }}></TableCell>
            {levels.map((level) => (
              <TableCell key={level.value} align="center">
                {level.label}
              </TableCell>
            ))}
          </TableRow>
        </TableHead>
        <TableBody>
          {questions.map((question) => (
            <TableRow key={question.id}>
              <TableCell component="th" scope="row">
                {question.text}
              </TableCell>
              {levels.map((level) => (
                <TableCell key={level.value} align="center">
                  <RadioGroup
                    value={getCurrentValue(question.id)}
                    onChange={(e) =>
                      handleResponseChange(question.id, e.target.value)
                    }
                  >
                    <FormControlLabel
                      value={level.value}
                      control={<Radio />}
                      label=""
                      labelPlacement="top"
                      sx={{
                        margin: 0,
                      }}
                    />
                  </RadioGroup>
                </TableCell>
              ))}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
};

export default function Page() {
  const { data: session, status } = useSession();
  const [successfullySubmitted, setSuccessfullySubmitted] = useState<boolean>();
  const [activeStep, setActiveStep] = useState<number>(0);
  const [formData, setFormData] = useState<CareerPrepSkillsAssessmentDTO>({
    jobseekerId: "",
    basicInformation: {
      pronouns: "",
      expectedEduCompletion: TimeUntilCompletion.NA,
    },
    workExperienceAndMaterials: {
      hasWorkExperience: false,
      hasResume: false,
      hasPortfolio: false,
      hasCoverLetter: false,
      hasLinkedInProfile: false,
      experienceWithApplying: false,
      experienceWithInterviewing: false,
    },
    technicalSelfAssessment: {
      interestPathway: CareerPrepPathways.CYBERSECURITY,
      skillRatings: {},
    },
    durableSkills: {
      emotionManagement: SkillLevel.Fair,
      empathy: SkillLevel.Fair,
      goalSetting: SkillLevel.Fair,
      timeManagement: SkillLevel.Fair,
      adaptability: SkillLevel.Fair,
      criticalThinking: SkillLevel.Fair,
      creativity: SkillLevel.Fair,
      resilience: SkillLevel.Fair,
      communication: SkillLevel.Fair,
      activeListening: SkillLevel.Fair,
      conflictResolution: SkillLevel.Fair,
      nonverbalCommunication: SkillLevel.Fair,
      teamwork: SkillLevel.Fair,
      trustBuilding: SkillLevel.Fair,
      leadership: SkillLevel.Fair,
      perspectiveTaking: SkillLevel.Fair,
      culturalAwareness: SkillLevel.Fair,
      relationshipBuilding: SkillLevel.Fair,
      documentationSkills: SkillLevel.Fair,
    },
    professionalBrandingAndJobMarketReadiness: {
      personalBrand: AgreementLevel.Neutral,
      onlinePresence: AgreementLevel.Neutral,
      elevatorPitch: AgreementLevel.Neutral,
      resumeEffectiveness: AgreementLevel.Neutral,
      coverLetterEffectiveness: AgreementLevel.Neutral,
      interviewExperience: AgreementLevel.Neutral,
      responseTechnique: AgreementLevel.Neutral,
      followUpImportance: AgreementLevel.Neutral,
      onlineNetworking: AgreementLevel.Neutral,
      eventNetworking: AgreementLevel.Neutral,
      relationshipManagement: AgreementLevel.Neutral,
      jobSearchStrategy: AgreementLevel.Neutral,
      materialDistribution: AgreementLevel.Neutral,
      networkingTechniques: AgreementLevel.Neutral,
      onboardingBestPractices: AgreementLevel.Neutral,
      developmentPlan: AgreementLevel.Neutral,
      mentorship: AgreementLevel.Neutral,
    },
  });

  const steps: string[] = [
    "Basic Information",
    "Work Experience",
    "Technical Skills",
    "Durable Skills",
    "Professional Branding and Job Market Readiness",
  ];

  useEffect(() => {
    const initializeFormFields = async () => {
      if (!session?.user.id) return;
      if (status === "authenticated") {
        const { id, jobseekerId } = session.user;
        try {
          if (!jobseekerId) return;
          const [coverLetterUrl, resumeUrl] = await Promise.all([
            fetch(`/api/jobseekers/coverLetter/get/${id}`),
            fetch(`/api/jobseekers/resume/get/${id}`),
          ]);

          if (resumeUrl.ok) {
            setFormData({
              ...formData,
              workExperienceAndMaterials: {
                ...formData.workExperienceAndMaterials,
                hasResume: true,
              },
            });
          }
          if (coverLetterUrl.ok) {
            setFormData({
              ...formData,
              workExperienceAndMaterials: {
                ...formData.workExperienceAndMaterials,
                hasCoverLetter: true,
              },
            });
          }
          setFormData({ ...formData, jobseekerId: jobseekerId });
        } catch (error) {
          console.error(error);
        }
      }
    };
    initializeFormFields();
  }, [session?.user?.id]);

  const handleNext = (): void => {
    setActiveStep((prevStep) => prevStep + 1);
    window.scrollTo({ top: 0, behavior: "instant" });
  };

  const handleBack = (): void => {
    setActiveStep((prevStep) => prevStep - 1);
    window.scrollTo({ top: 0, behavior: "instant" });
  };

  const handleInputChange = (
    event:
      | React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
      | SelectChangeEvent<TimeUntilCompletion>,
  ) => {
    const { name, value } = event.target;
    const parsedValue =
      event.target instanceof HTMLInputElement && event.target.type === "radio"
        ? value === "true"
        : value;

    setFormData((prevData) => {
      const keys = name.split("."); // Split the name by dot notation
      const updatedData = { ...prevData };

      // Recursively update nested properties
      keys.reduce((acc: any, key, index) => {
        if (index === keys.length - 1) {
          acc[key] = parsedValue;
        } else {
          acc[key] = { ...acc[key] };
        }
        return acc[key];
      }, updatedData);

      return updatedData;
    });
  };

  const handleTableChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    const parsedValue = Number(value);

    setFormData((prevData) => {
      const keys = name.split(".");
      const updatedData = { ...prevData };

      keys.reduce((acc: any, key, index) => {
        if (index === keys.length - 1) {
          acc[key] = parsedValue;
        } else {
          acc[key] = { ...acc[key] };
        }
        return acc[key];
      }, updatedData);

      return updatedData;
    });
  };

  const handlePathwayChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { value } = event.target;
    setFormData((prevData) => ({
      ...prevData,
      technicalSelfAssessment: {
        ...prevData.technicalSelfAssessment,
        interestPathway: value as CareerPrepPathways,
      },
    }));
  };

  const renderBasicInformation = (): JSX.Element => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Basic Information
      </Typography>
      <Grid container spacing={2}>
        <Grid size={12}>
          <FormControl component="fieldset" sx={{ mb: 2 }}>
            <FormLabel>What are your preferred pronouns?</FormLabel>
            <TextField
              fullWidth
              id="pronouns"
              label="Pronouns"
              name="basicInformation.pronouns"
              value={formData.basicInformation.pronouns}
              placeholder="They/Them"
              onChange={handleInputChange}
              sx={{ mb: 2 }}
            />
          </FormControl>
        </Grid>

        <Grid size={12}>
          <FormControl component="fieldset" sx={{ mb: 2 }}>
            <FormLabel>When do you expect to finish your education?</FormLabel>
            <Select
              id="expected-edu-completion"
              label="Estimated finish"
              name="basicInformation.expectedEduCompletion"
              value={formData.basicInformation.expectedEduCompletion}
              onChange={handleInputChange}
            >
              {Object.entries(TimeUntilCompletion).map(([value, label]) => (
                <MenuItem key={value + label} id={value + label} value={label}>
                  {label}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>
    </Box>
  );

  const renderWorkExperience = (): JSX.Element => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Work Experience
      </Typography>
      <Grid container spacing={2}>
        <Grid size={12}>
          <FormControl component="fieldset" sx={{ mb: 2 }}>
            <FormLabel>Do you have previous work experience?</FormLabel>
            <RadioGroup
              name="workExperienceAndMaterials.hasWorkExperience"
              onChange={handleInputChange}
              value={formData.workExperienceAndMaterials.hasWorkExperience}
            >
              <FormControlLabel value={true} control={<Radio />} label="Yes" />
              <FormControlLabel value={false} control={<Radio />} label="No" />
            </RadioGroup>
          </FormControl>
        </Grid>

        <Grid size={12}>
          <FormControl component="fieldset" sx={{ mb: 2 }}>
            <FormLabel>
              Do you have experience applying for tech jobs?
            </FormLabel>
            <RadioGroup
              name="workExperienceAndMaterials.experienceWithApplying"
              onChange={handleInputChange}
              value={formData.workExperienceAndMaterials.experienceWithApplying}
            >
              <FormControlLabel value={true} control={<Radio />} label="Yes" />
              <FormControlLabel value={false} control={<Radio />} label="No" />
            </RadioGroup>
          </FormControl>
        </Grid>

        <Grid size={12}>
          <FormControl component="fieldset" sx={{ mb: 2 }}>
            <FormLabel>Have you participated in a job interview?</FormLabel>
            <RadioGroup
              name="workExperienceAndMaterials.experienceWithInterviewing"
              onChange={handleInputChange}
              value={
                formData.workExperienceAndMaterials.experienceWithInterviewing
              }
            >
              <FormControlLabel value={true} control={<Radio />} label="Yes" />
              <FormControlLabel value={false} control={<Radio />} label="No" />
            </RadioGroup>
          </FormControl>
        </Grid>
      </Grid>
    </Box>
  );

  const renderTechnicalSelfAssessment = (): JSX.Element => {
    return (
      <Box sx={{ p: 2 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Technical Skills Assessment
        </Typography>
        <Typography sx={{ mb: 2 }}>
          Your responses will help us understand your current skills and
          identify areas where you might need support in reaching your career
          goals.
        </Typography>
        <FormControl component="fieldset" sx={{ mb: 4 }}>
          <FormLabel>What technology pathway most interests you?</FormLabel>
          <RadioGroup
            name="technicalSelfAssessment.interestPathway"
            onChange={handlePathwayChange}
            value={formData.technicalSelfAssessment.interestPathway}
          >
            {Object.entries(CareerPrepPathways).map(([value, label]) => (
              <FormControlLabel
                key={value + label}
                value={label}
                control={<Radio />}
                label={label}
              />
            ))}
          </RadioGroup>
        </FormControl>
        {formData.technicalSelfAssessment.interestPathway ==
          CareerPrepPathways.CYBERSECURITY && (
          <EvaluationTable
            questions={[
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
            ]}
            section="technicalSelfAssessment.skillRatings.cybersecurity"
            onChange={handleTableChange}
            labels={SkillProficiencyLabels}
            formData={formData}
          />
        )}
        {formData.technicalSelfAssessment.interestPathway ==
          CareerPrepPathways.DATA_ANALYTICS && (
          <EvaluationTable
            questions={[
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
            ]}
            section="technicalSelfAssessment.skillRatings.dataAnalytics"
            onChange={handleTableChange}
            labels={SkillProficiencyLabels}
            formData={formData}
          />
        )}
        {formData.technicalSelfAssessment.interestPathway ==
          CareerPrepPathways.IT_CLOUD_SUPPORT && (
          <EvaluationTable
            questions={[
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
            ]}
            section="technicalSelfAssessment.skillRatings.itAndCloudComputing"
            onChange={handleTableChange}
            labels={SkillProficiencyLabels}
            formData={formData}
          />
        )}
        {formData.technicalSelfAssessment.interestPathway ==
          CareerPrepPathways.SOFTWARE_DEVELOPER && (
          <EvaluationTable
            questions={[
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
            ]}
            section="technicalSelfAssessment.skillRatings.softwareDevelopment"
            onChange={handleTableChange}
            labels={SkillProficiencyLabels}
            formData={formData}
          />
        )}
      </Box>
    );
  };

  const renderDurableSkills = (): JSX.Element => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Durable Skills Assessment
      </Typography>
      <Typography sx={{ mb: 2 }}>
        Soft skills are undergoing a rebranding, and in lieu of the word soft,
        many people are now referring to them as durable. But that&apos;s not
        all—there has been a considerable shift in the demand of durable skills
        as more employers see their increase in value, and more hiring managers
        switch to a skills-based hiring model.
      </Typography>
      <Typography>
        Remember:Your responses will help us understand your current skills and
        identify areas where you might need support in reaching your career
        goals.
      </Typography>
      <Grid container spacing={2}>
        {
          <EvaluationTable
            questions={[
              {
                id: "emotionManagement",
                text: "Understanding and managing my own emotions.",
              },
              {
                id: "empathy",
                text: "Empathizing with and understanding the emotions of others.",
              },
              {
                id: "goalSetting",
                text: "Setting and achieving goals effectively.",
              },
              {
                id: "timeManagement",
                text: "Managing my time efficiently and prioritizing tasks.",
              },
              {
                id: "adaptability",
                text: "Learning from my mistakes and adapting to new situations.",
              },
              {
                id: "criticalThinking",
                text: "Thinking critically and solving problems effectively.",
              },
              {
                id: "creativity",
                text: "Generating new and innovative ideas.",
              },
              {
                id: "resilience",
                text: "Persisting through challenges and setbacks.",
              },
              {
                id: "communication",
                text: "Communicating clearly and effectively, both verbally and in writing.",
              },
              {
                id: "activeListening",
                text: "Actively listening to others and understanding their perspectives.",
              },
              {
                id: "conflictResolution",
                text: "Resolving conflicts peacefully and constructively.",
              },
              {
                id: "nonverbalCommunication",
                text: "Using nonverbal communication effectively to convey my message.",
              },
              {
                id: "teamwork",
                text: "Working effectively as part of a team and collaborating with others.",
              },
              {
                id: "trustBuilding",
                text: "Building trust and rapport with others.",
              },
              {
                id: "leadership",
                text: "Taking on leadership roles when appropriate and following the lead of others when necessary.",
              },
              {
                id: "perspectiveTaking",
                text: "Understanding and appreciating the perspectives of others, even when they differ from my own.",
              },
              {
                id: "culturalAwareness",
                text: "Being aware of cultural differences and adapting my communication style accordingly.",
              },
              {
                id: "relationshipBuilding",
                text: "Building and maintaining strong relationships with others.",
              },
              {
                id: "documentationSkills",
                text: "Creating clear and meaningful documentation or presentations to clearly communicate an idea.",
              },
            ]}
            section="durableSkills"
            onChange={handleTableChange}
            labels={SkillLevelLabels}
            formData={formData}
          />
        }
      </Grid>
    </Box>
  );

  const renderProfessionalBrandingAndJobMarketReadiness = (): JSX.Element => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Professional Branding & Job Market Readiness
      </Typography>
      <Typography>
        Remember: Your responses will help us understand your current skills and
        identify areas where you might need support in reaching your career
        goals.
      </Typography>
      <Grid container spacing={2}>
        {
          <EvaluationTable
            questions={[
              {
                id: "personalBrand",
                text: "I have a clear and consistent personal brand that reflects my skills, values, and career goals.",
              },
              {
                id: "onlinePresence",
                text: "I manage my online presence effectively, including my social media an networking profiles.",
              },
              {
                id: "elevatorPitch",
                text: "I can deliver a concise and compelling elevator pitch that highlights my skills and career goals.",
              },
              {
                id: "resumeEffectiveness",
                text: "I have a resume that effectively showcases my skills, experiences, and achievements.",
              },
              {
                id: "coverLetterEffectiveness",
                text: "I have a cover letter template and am successful at tailoring it to each job application to highlight my relevant qualifications.",
              },
              {
                id: "interviewExperience",
                text: "I have experience with different types of interviews, including technical, behavioral, virtual, and in-person interviews.",
              },
              {
                id: "responseTechnique",
                text: "I am familiar with and confident in my ability to use effective response techniques to answer interview questions.",
              },
              {
                id: "followUpImportance",
                text: "I understand the importance of following up after an interview and can effectively do so.",
              },
              {
                id: "onlineNetworking",
                text: "I am familiar with best practices for using online platforms to connect with potential employers and industry professionals.",
              },
              {
                id: "eventNetworking",
                text: "I am confident attending industry events and career fairs to expand my professional network.",
              },
              {
                id: "relationshipManagement",
                text: "I can successfully maintain and nurture professional relationships over time.",
              },
              {
                id: "jobSearchStrategy",
                text: "I am able to effectively search for job opportunities and tailor my job search strategy to my career goals.",
              },
              {
                id: "materialDistribution",
                text: "I am familiar with best practices for distributing professional materials to potential employers.",
              },
              {
                id: "networkingTechniques",
                text: "I am able to use effective networking techniques, such as informational interviewing and active listening. ",
              },
              {
                id: "onboardingBestPractices",
                text: "I am familiar with best practices for onboarding and can effectively adapt to a new role.",
              },
              {
                id: "developmentPlan",
                text: "I have experience with creating and implementing a personal development plan in a new role to enhance my skills and career prospects.",
              },
              {
                id: "mentorship",
                text: "I can confidently seek mentorship and coaching within my networks to support my career development.",
              },
            ]}
            section="professionalBrandingAndJobMarketReadiness"
            onChange={handleTableChange}
            labels={AgreementLevelLabels}
            formData={formData}
          />
        }
      </Grid>
    </Box>
  );

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>,
  ): Promise<void> => {
    e.preventDefault();
    const response = await fetch(
      "/api/jobseekers/career-prep/skill-assessment/submit/",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      },
    );
    if (response.ok) {
      setSuccessfullySubmitted(true);
      window.scrollTo({ top: 0, behavior: "instant" });
    } else {
      setSuccessfullySubmitted(false);
    }
  };

  const getStepContent = (step: number): JSX.Element => {
    switch (step) {
      case 0:
        return renderBasicInformation();
      case 1:
        return renderWorkExperience();
      case 2:
        return renderTechnicalSelfAssessment();
      case 3:
        return renderDurableSkills();
      case 4:
        return renderProfessionalBrandingAndJobMarketReadiness();
      default:
        throw new Error("Unknown step");
    }
  };

  return (
    <>
      {" "}
      {successfullySubmitted ? (
        <>
          <Box className="flex justify-center">
            <Box
              style={{ height: "100vh" }}
              className="profile-form-section main-content"
            >
              <Confetti />
              <h1>Next Steps</h1>
              <Typography sx={{ pt: 3, mb: 3 }}>
                {
                  "Thank you for completing the skills assessment! A dedicated Career Navigator will review your results and create a personalized Professional Development Plan tailored to your needs. You’ll receive an email notification when your plan is ready."
                }
              </Typography>
              <Grid container>
                <PillButton href="/services/jobseekers/dashboard">
                  Go to Dashboard
                </PillButton>
              </Grid>
            </Box>
          </Box>
        </>
      ) : (
        <Box sx={{ p: 3, my: 4 }}>
          <Typography variant="h4" align="center" sx={{ mb: 4 }}>
            Career Prep Skills Assessment
          </Typography>
          {activeStep == 0 && (
            <Typography sx={{ mb: 4 }}>
              This assessment will evaluate your technical, durable, and career
              readiness skills to help us create a personalized professional
              development plan tailored to your specific needs and goals. Your
              responses will help us understand your current skills, strengths,
              and areas for improvement where you might need support in reaching
              your career goals. To help us provide the best possible guidance,
              please ensure your responses accurately represent you in this
              present moment. Let's work together to unlock your potential!
            </Typography>
          )}
          <Stepper
            activeStep={activeStep}
            sx={{ display: { xs: "none", md: "flex" }, mb: 4 }}
          >
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>
          <Typography
            sx={{
              display: { xs: "flex", md: "none" },
              mb: 4,
              justifySelf: "center",
            }}
          >
            {"Progress: " + activeStep + " / " + steps.length}
          </Typography>
          <form onSubmit={handleSubmit}>
            {getStepContent(activeStep)}

            <Grid container sx={{ justifyContent: "space-between", mt: 4 }}>
              <PillButton disabled={activeStep === 0} onClick={handleBack}>
                Back
              </PillButton>
              <Box>
                {activeStep === steps.length - 1 && (
                  <PillButton type="submit">Submit</PillButton>
                )}
                {activeStep !== steps.length - 1 && (
                  <PillButton onClick={handleNext}>Next</PillButton>
                )}
              </Box>
            </Grid>
          </form>
        </Box>
      )}
    </>
  );
}
