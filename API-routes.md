# API Routes

This section provides detailed information on the available API routes for the Computing for All Talent Finder application.

---

### Jobseeker Routes

---

#### Jobseeker List View Query

_This route is used to generate the cards on the talent-search page. On the server side it filters based on skills and years
work experience. Also, it will also filter out any jobseeker accounts that have been marked for deletion._

**Endpoint**: `/api/jobseekers/query`

**Method**: `POST`

##### Sample Request Object

```json
{
  "skills": [],
  "yearsWorkExp": 0
}
```

##### Sample Response Object

```json
[
  {
    "jobseeker_id": "d193e1c1-241b-46f9-ac78-d8076ae357d9",
    "user_id": "84579f62-755f-429b-a141-60b8093b6544",
    "intro_headline": "\n    Hi, my name is Courtney Lebsack. I am a highly skilled Future Accountability Analyst with over 7 years of experience in the industry.\n    I have a proven track record of success at Wehner Inc, where I contributed to numerous high-profile projects.\n    My key skills include auxiliary array, solid state monitor, online sensor.\n  ",
    "pathways": {
      "pathway_id": "01b09b15-428c-4eb8-96de-ae9933f51842",
      "pathway_title": "Cloud Computing"
    },
    "users": {
      "user_id": "84579f62-755f-429b-a141-60b8093b6544",
      "role": "Jobseeker",
      "first_name": "Courtney",
      "last_name": "Lebsack",
      "photo_url": "https://randomuser.me/api/portraits/men/55.jpg"
    },
    "jobseeker_education": [],
    "jobseeker_has_skills": [
      {
        "skills": {
          "skill_id": "80b21e5f-1905-4c75-9a3d-e43692845295",
          "skill_name": "Federated Identity Management",
          "skill_info_url": "https://lightcast.io/open-skills/skills/KS123W065B95QJ1G00BL"
        }
      },
      {
        "skills": {
          "skill_id": "bd9722e6-872c-424a-8a90-9b1cef55b0aa",
          "skill_name": "NonStop SQL",
          "skill_info_url": "https://lightcast.io/open-skills/skills/KS1272N6NN3ZKFXYCFL4"
        }
      },
      {
        "skills": {
          "skill_id": "c9e3a4d6-97b1-4d82-a132-fc2f253ddb4b",
          "skill_name": "Internet Transit",
          "skill_info_url": "https://lightcast.io/open-skills/skills/KS125BY6GHQ5SPTKQ7TB"
        }
      },
      {
        "skills": {
          "skill_id": "89c6a12e-b094-4e95-83ae-1e9d58a932a5",
          "skill_name": "BlackBerry OS",
          "skill_info_url": "https://lightcast.io/open-skills/skills/KS1212J609C8JTL1H9W1"
        }
      },
      {
        "skills": {
          "skill_id": "8e59e0b3-a0af-46bf-989e-e86a5d045e44",
          "skill_name": "Cryptographic Protocols",
          "skill_info_url": "https://lightcast.io/open-skills/skills/KS123JD6CYFD6JNW67DX"
        }
      }
    ]
  }
]
```

## Profile Creation APIs

---

### Introduction Page

---

#### Create or Update Introduction Page

_This route is meant to be used with the `profile-creation/jobseeker/intro page` to create or update new entries. It
creates or updates all the data in entire introduction page._

**Endpoint**: `/api/jobseekers/account/introduction/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `JsIntroPostDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "photoUrl": "https://example.com/photo.jpg",
  "firstName": "Gary",
  "lastName": "Larson",
  "birthDate": "2000-01-01T00:00:00.000Z",
  "phoneCountryCode": "+1",
  "phone": "(360) 322-9617",
  "zipCode": "98101",
  "state": "WA",
  "city": "Seattle",
  "county": "King",
  "email": "gary@computingforall.org",
  "introHeadline": "Aspiring Software Developer",
  "currentJobTitle": "Junior Developer",
  "resumeUrl": "https://example.com/resume.pdf"
}
```

##### Sample Response

**DTO**: loadIntroPage property uses DTO `JsIntroDTO`

```json
{
  "success": true,
  "result": {
    "loadIntroPage": {
      "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
      "photoUrl": "https://example.com/photo.jpg",
      "firstName": "Gary",
      "lastName": "Larson",
      "birthDate": "2000-01-01T00:00:00.000Z",
      "phoneCountryCode": "1",
      "phone": "+13603229617",
      "zipCode": "98101",
      "state": "WA",
      "city": "Seattle",
      "county": "King",
      "email": "gary@computingforall.org",
      "introHeadline": "Aspiring Software Developer",
      "currentJobTitle": "Junior Developer",
      "resumeUrl": "https://example.com/resume.pdf"
    },
    "meta": {
      "emailVerified": null,
      "createdAt": "2024-08-08T07:20:17.273Z",
      "pathwayId": "79608104-d50e-4d0f-b541-2a9de7bc0f89",
      "jobseekerId": "da7339e0-8cf9-4cdb-b02e-97ee598c8c1d",
      "contactAddressId": "356b592c-663e-4201-8a8a-540ed4d2d957",
      "isMarkedDeletion": null
    }
  }
}
```

---

#### Read Jobseeker Introduction Page

_This route is meant to be used with the `/edit-profile/jobseeker/intro` page for initial load if there is preexisting
data._

**Endpoint**: `/api/jobseekers/account/introduction/get/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: result.loadIntroPage property uses DTO `JsIntroDTO`

```json
{
  "success": true,
  "result": {
    "loadIntroPage": {
      "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
      "photoUrl": "https://example.com/photo.jpg",
      "firstName": "Gary",
      "lastName": "Larson",
      "birthDate": "2000-01-01T00:00:00.000Z",
      "phoneCountryCode": "1",
      "phone": "+13603229617",
      "zipCode": "98101",
      "state": "WA",
      "city": "Seattle",
      "county": "King",
      "email": "gary@computingforall.org",
      "introHeadline": "Aspiring Software Developer",
      "currentJobTitle": "Junior Developer",
      "resumeUrl": "https://example.com/resume.pdf"
    },
    "meta": {
      "emailVerified": null,
      "createdAt": "2024-08-08T07:20:17.273Z",
      "pathwayId": "79608104-d50e-4d0f-b541-2a9de7bc0f89",
      "jobseekerId": "da7339e0-8cf9-4cdb-b02e-97ee598c8c1d",
      "contactAddressId": "356b592c-663e-4201-8a8a-540ed4d2d957",
      "isMarkedDeletion": null
    }
  }
}
```

---

### Education Page

---

#### Create or Update Jobseeker Education Page

_This route is meant to be used with the `/edit-profile/jobseeker/education` page for creating or updating any data on
this page._

If the institution does not currently exist in our database an entry is created in the `edu_institutions` table using
the institutionName property. There should exist a drop-down available for jobseekers to use to choose their educational
institution.

> NOTE: For optimization we may want to implement individual CREATE routes for each of the following: certifications,
> project experiences, work experiences.

**Endpoint**: `/api/jobseekers/account/edu-info/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `JsEducationDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "currentEdProgram": "College",
  "highestLevelOfStudy": "Bachelor's Degree",
  "currentGrade": "Junior",
  "isEnrolledEdProgram": true,
  "schools": [
    {
      "jobseekerEdId": "53d66079-60e2-46a2-9214-e86e2f766734",
      "edInstitutionId": "077291f4-a2d6-484c-82bc-ae96ba036761",
      "institutionName": "North Seattle College",
      "edProgram": "College",
      "edSystem": null,
      "isEnrolled": true,
      "startDate": "2024-12-01T00:00:00.000Z",
      "gradDate": "2028-07-01T00:00:00.000Z",
      "degreeType": "BachelorsDegree",
      "major": "Computer Science",
      "minor": "asdf",
      "description": "Studied various computer science topics and applied them in practical projects."
    },
    {
      "jobseekerEdId": "dc9fb674-1e7c-46c3-a3d2-5bc72e5dd4c6",
      "edInstitutionId": "24f31a6d-2c7b-48d2-88ee-cf65edbd5fa0",
      "institutionName": "CFA PAP",
      "edProgram": "PreApprenticeship",
      "edSystem": "System ABC",
      "isEnrolled": false,
      "startDate": "2022-06-01T00:00:00.000Z",
      "gradDate": "2028-06-01T00:00:00.000Z",
      "degreeType": "None",
      "major": null,
      "minor": null,
      "description": "Studied various computer science topics and applied them in practical projects."
    }
  ],
  "certifications": [
    {
      "certId": "5b97ce22-6f37-4ea1-91c4-9f41e513d8e0",
      "name": "Certified JavaScript Developer",
      "logoUrl": "",
      "issuingOrg": "XYZ Institute",
      "credentialId": "CJD-002",
      "credentialUrl": "http://credential.u",
      "issueDate": "2023-01-01T00:00:00.000Z",
      "expiryDate": "2025-01-01T00:00:00.000Z",
      "description": "Certification"
    }
  ],
  "projects": [
    {
      "projectId": "b5a4f51c-90e5-4b6e-9a5a-83f1c8f789c6",
      "jobseekerId": "7e1db701-f79a-43e5-a434-23dd6690fb57",
      "projTitle": "Web Development Project",
      "projectRole": "backend dev",
      "startDate": "2022-01-01T00:00:00.000Z",
      "completionDate": "2022-06-01T00:00:00.000Z",
      "problemSolvedDescription": "Developed a web application using React and Node.js.",
      "teamSize": "8",
      "repoUrl": "https://www.repo.url",
      "demoUrl": "https:///www.demo.url",
      "skills": [
        {
          "skill_id": "356e0040-8400-49a0-b772-6f6475776612",
          "skill_name": "JavaScript",
          "skill_info_url": "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language"
        },
        {
          "skill_id": "38943cce-679d-408f-9fb1-6d054012e54f",
          "skill_name": ".NET Assemblies",
          "skill_info_url": "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X"
        }
      ]
    }
  ]
}
```

##### Sample Response

**DTO**: result property adheres to`JsEducationDTO`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "currentEdProgram": "College",
    "highestLevelOfStudy": "Bachelor's Degree",
    "currentGrade": "Junior",
    "isEnrolledEdProgram": false,
    "schools": [
      {
        "jobseekerEdId": "53d66079-60e2-46a2-9214-e86e2f766734",
        "edInstitutionId": "077291f4-a2d6-484c-82bc-ae96ba036761",
        "edProgram": "College",
        "edSystem": null,
        "isEnrolled": true,
        "startDate": "2024-12-01T00:00:00.000Z",
        "gradDate": "2028-07-01T00:00:00.000Z",
        "degreeType": null,
        "major": "Computer Science",
        "minor": "asdf",
        "description": "Studied various computer science topics and applied them in practical projects."
      },
      {
        "jobseekerEdId": "dc9fb674-1e7c-46c3-a3d2-5bc72e5dd4c6",
        "edInstitutionId": "24f31a6d-2c7b-48d2-88ee-cf65edbd5fa0",
        "edProgram": null,
        "edSystem": "System ABC",
        "isEnrolled": true,
        "startDate": "2022-06-01T00:00:00.000Z",
        "gradDate": "2028-06-01T00:00:00.000Z",
        "degreeType": "None",
        "major": null,
        "minor": null,
        "description": "Studied various computer science topics and applied them in practical projects."
      }
    ],
    "certifications": [
      {
        "certId": "5b97ce22-6f37-4ea1-91c4-9f41e513d8e0",
        "name": "Certified JavaScript Developer",
        "logoUrl": null,
        "issuingOrg": "XYZ Institute",
        "credentialId": "CJD-002",
        "credentialUrl": "http://credential.u",
        "issueDate": "2023-01-01T00:00:00.000Z",
        "expiryDate": "2023-01-01T00:00:00.000Z",
        "description": "Certification"
      }
    ],
    "projects": [
      {
        "projectId": "b5a4f51c-90e5-4b6e-9a5a-83f1c8f789c6",
        "jobseekerId": "7e1db701-f79a-43e5-a434-23dd6690fb57",
        "projTitle": "Web Development Project",
        "projectRole": "backend dev",
        "startDate": "2022-01-01T00:00:00.000Z",
        "completionDate": "2022-06-01T00:00:00.000Z",
        "problemSolvedDescription": "Developed a web application using React and Node.js.",
        "teamSize": "8",
        "repoUrl": "https://www.repo.url",
        "demoUrl": "https:///www.demo.url",
        "skills": [
          {
            "skill_id": "356e0040-8400-49a0-b772-6f6475776612",
            "skill_name": "JavaScript",
            "skill_info_url": "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language"
          },
          {
            "skill_id": "38943cce-679d-408f-9fb1-6d054012e54f",
            "skill_name": ".NET Assemblies",
            "skill_info_url": "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X"
          }
        ]
      }
    ]
  }
}
```

---

#### Read Jobseeker Education Profile Page

_This route is meant to be used with the `/edit-profile/jobseeker/education` page for initial loading of preexisting
data, if any._

**Endpoint**: `/api/jobseekers/account/edu-info/get/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property adheres to type `JsEducationDTO`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "currentEdProgram": "College",
    "highestLevelOfStudy": "Bachelor's Degree",
    "currentGrade": "Junior",
    "isEnrolledEdProgram": false,
    "schools": [
      {
        "jobseekerEdId": "53d66079-60e2-46a2-9214-e86e2f766734",
        "edInstitutionId": "077291f4-a2d6-484c-82bc-ae96ba036761",
        "institutionName": "North Seattle College",
        "edProgram": "College",
        "edSystem": null,
        "isEnrolled": true,
        "startDate": "2024-12-01T00:00:00.000Z",
        "gradDate": "2028-07-01T00:00:00.000Z",
        "degreeType": null,
        "major": "Computer Science",
        "minor": "asdf",
        "description": "Studied various computer science topics and applied them in practical projects."
      },
      {
        "jobseekerEdId": "dc9fb674-1e7c-46c3-a3d2-5bc72e5dd4c6",
        "edInstitutionId": "24f31a6d-2c7b-48d2-88ee-cf65edbd5fa0",
        "institutionName": "CFA PAP",
        "edProgram": null,
        "edSystem": "System ABC",
        "isEnrolled": true,
        "startDate": "2022-06-01T00:00:00.000Z",
        "gradDate": "2028-06-01T00:00:00.000Z",
        "degreeType": "None",
        "major": null,
        "minor": null,
        "description": "Studied various computer science topics and applied them in practical projects."
      }
    ],
    "certifications": [
      {
        "certId": "5b97ce22-6f37-4ea1-91c4-9f41e513d8e0",
        "name": "Certified JavaScript Developer",
        "logoUrl": null,
        "issuingOrg": "XYZ Institute",
        "credentialId": "CJD-002",
        "credentialUrl": "http://credential.u",
        "issueDate": "2023-01-01T00:00:00.000Z",
        "expiryDate": "2023-01-01T00:00:00.000Z",
        "description": "Certification"
      }
    ],
    "projects": [
      {
        "projectId": "b5a4f51c-90e5-4b6e-9a5a-83f1c8f789c6",
        "projTitle": "Web Development Project",
        "projectRole": "backend dev",
        "startDate": "2022-01-01T00:00:00.000Z",
        "completionDate": "2022-06-01T00:00:00.000Z",
        "problemSolvedDescription": "Developed a web application using React and Node.js.",
        "teamSize": "8",
        "repoUrl": "https://www.repo.url",
        "demoUrl": "https:///www.demo.url",
        "skills": [
          {
            "skill_id": "356e0040-8400-49a0-b772-6f6475776612",
            "skill_name": "JavaScript",
            "skill_info_url": "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language"
          },
          {
            "skill_id": "38943cce-679d-408f-9fb1-6d054012e54f",
            "skill_name": ".NET Assemblies",
            "skill_info_url": "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X"
          }
        ]
      }
    ]
  }
}
```

---

#### Delete Jobseeker Education Record

_This will delete a jobseeker education record. It is intended for use within the `/edit-profile/jobseeker/education`
page using the key from the respective jobseeker education entry._

**Endpoint**: `/api/jobseekers/education/remove/<eduId>`

**Method**: `DELETE`

##### Sample Response

**DTO**: result property is type `jobseekers_education` generated by PrismaClient from schema.prisma

```json
{
  "success": true,
  "result": {
    "jobseekerEdId": "53d66079-60e2-46a2-9214-e86e2f766734",
    "jobseekerId": "48586cd0-74ba-4da0-9bb2-2862a5c7ca5b",
    "edInstitutionId": "077291f4-a2d6-484c-82bc-ae96ba036761",
    "edProgram": "College",
    "edSystem": null,
    "isEnrolled": true,
    "startDate": "2024-12-01T00:00:00.000Z",
    "gradDate": "2028-07-01T00:00:00.000Z",
    "degreeType": "BachelorsDegree",
    "major": "Computer Science",
    "minor": "asdf",
    "description": "Studied various computer science topics and applied them in practical projects."
  }
}
```

---

#### Delete Jobseeker Certification

_This will delete a jobseeker certification record. It is intended for use within
the `/edit-profile/jobseeker/education` page using the key from the respective certification entry._

**Endpoint**: `/api/jobseekers/certifications/remove/<certificateId>`

##### Sample Response

**DTO**: result property is `certificates` type generated by PrismaClient from schema.prisma

```json
{
  "success": true,
  "result": {
    "certId": "5b97ce22-6f37-4ea1-91c4-9f41e513d8e0",
    "jobSeekerId": "48586cd0-74ba-4da0-9bb2-2862a5c7ca5b",
    "name": "Certified JavaScript Developer",
    "logoUrl": null,
    "issuingOrg": "XYZ Institute",
    "credentialId": "CJD-002",
    "credentialUrl": "http://credential.u",
    "issueDate": "2023-01-01T00:00:00.000Z",
    "expiryDate": "2025-01-01T00:00:00.000Z",
    "description": "Certification"
  }
}
```

---

#### Delete Jobseeker Project Experience

_This will delete a jobseeker project experience record. It is intended for use within
the `/edit-profile/jobseeker/education` page using the key from the respective project experience entry. It will also
delete the associated skills from within the `project_has_skills` table._

**Endpoint**: `/api/jobseekers/projects/remove/<projectId>`

**Method**: `DELETE`

##### Sample Response

**DTO**: result property is `ProjectExperiences` type generated by PrismaClient from schema.prisma

```json
{
  "success": true,
  "result": {
    "projectId": "b5a4f51c-90e5-4b6e-9a5a-83f1c8f789c6",
    "jobseekerId": "da7339e0-8cf9-4cdb-b02e-97ee598c8c1d",
    "projTitle": "Web Development Project",
    "projectRole": "backend dev",
    "startDate": "2022-01-01T00:00:00.000Z",
    "completionDate": "2022-06-01T00:00:00.000Z",
    "problemSolvedDescription": "Developed a web application using React and Node.js.",
    "teamSize": 8,
    "repoUrl": "https://www.repo.url",
    "demoUrl": "https:///www.demo.url",
    "skillsCount": {
      "count": 2
    }
  }
}
```

---

### Work Experience Page

---

#### Upsert Jobseeker Work Profile Page

_This route is meant to be used with the `/edit-profile/jobseeker/work-experience` page for creating or updating
data._

**Endpoint**: `/api/jobseekers/account/work-info/upsert`

**Method**: `POST`

##### Sample Request

> Currently, "techAreaId" is not available from the frontend. It is hardcoded into the seed.mjs file for this to work.
> Work experiences should contain a drop-down to determine the tech area for the work experience.

**DTO**: `JsWorkExpDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "yearsWorkExperience": "5",
  "amountInternshipExperience": "2",
  "isAuthorizedToWorkUsa": true,
  "requiresSponsorship": false,
  "workExperiences": [
    {
      "workId": "ddf90dca-5273-4651-aef3-340ea8494335",
      "company": "CFA",
      "jobTitle": "Backend Web Developer",
      "isCurrentJob": true,
      "startDate": "2020-01-01",
      "endDate": null,
      "responsibilities": "Coordinating and developing Project Factory projects",
      "isInternship": false,
      "techAreaId": "7acd2248-a2c3-4789-b414-a2463b75997a"
    },
    {
      "workId": "ddf90cad-5273-4651-aef3-340ea8494335",
      "company": "CFA",
      "jobTitle": "intern",
      "isCurrentJob": false,
      "startDate": "2022-01-01",
      "endDate": "2022-03-25",
      "responsibilities": "Microsoft Dynamics Plugins for admin workflow",
      "isInternship": true,
      "techAreaId": "4c376b09-38e2-4278-b70b-975837c43fe5"
    }
  ]
}
```

##### Sample Response

**DTO**: result property is `JsWorkExpDTO` type.

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "yearsWorkExperience": "5",
    "monthsInternshipExperience": "2",
    "isAuthorizedToWorkUsa": true,
    "requiresSponsorship": false,
    "workExperiences": [
      {
        "workId": "ddf90dca-5273-4651-aef3-340ea8494335",
        "jobseekerId": "48586cd0-74ba-4da0-9bb2-2862a5c7ca5b",
        "techAreaId": "7acd2248-a2c3-4789-b414-a2463b75997a",
        "company": "CFA",
        "isInternship": false,
        "jobTitle": "Backend Web Developer",
        "isCurrentJob": true,
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "responsibilities": "Coordinating and developing Project Factory projects"
      },
      {
        "workId": "ddf90cad-5273-4651-aef3-340ea8494335",
        "jobseekerId": "48586cd0-74ba-4da0-9bb2-2862a5c7ca5b",
        "techAreaId": "4c376b09-38e2-4278-b70b-975837c43fe5",
        "company": "CFA",
        "isInternship": true,
        "jobTitle": "intern",
        "isCurrentJob": false,
        "startDate": "2022-01-01T00:00:00.000Z",
        "endDate": "2022-03-25T00:00:00.000Z",
        "responsibilities": "Microsoft Dynamics Plugins for admin workflow"
      }
    ]
  }
}
```

---

#### Read Jobseeker Work Experience Profile Page

_This route is meant to be used with the `/edit-profile/jobseeker/work-experience` page for initial load of data, if
any._

**Endpoint**: `/api/jobseekers/account/work-info/get/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: Result property is type `JsWorkExpDTO`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "yearsWorkExperience": "5",
    "monthsInternshipExperience": "2",
    "isAuthorizedToWorkUsa": true,
    "requiresSponsorship": false,
    "workExperiences": [
      {
        "workId": "ddf90dca-5273-4651-aef3-340ea8494335",
        "jobseekerId": "a7e2b588-201a-4b2c-a35c-495ede76f840",
        "company": "CFA",
        "jobTitle": "Backend Web Developer",
        "isCurrentJob": true,
        "startDate": "2020-01-01T00:00:00.000Z",
        "endDate": null,
        "responsibilities": "Coordinating and developing Project Factory projects",
        "isInternship": false,
        "techAreaId": "7acd2248-a2c3-4789-b414-a2463b75997a"
      },
      {
        "workId": "ddf90cad-5273-4651-aef3-340ea8494335",
        "jobseekerId": "a7e2b588-201a-4b2c-a35c-495ede76f840",
        "company": "CFA",
        "jobTitle": "intern",
        "isCurrentJob": false,
        "startDate": "2022-01-01T00:00:00.000Z",
        "endDate": "2022-03-25T00:00:00.000Z",
        "responsibilities": "Microsoft Dynamics Plugins for admin workflow",
        "isInternship": true,
        "techAreaId": "4c376b09-38e2-4278-b70b-975837c43fe5"
      }
    ]
  }
}
```

---

#### Delete Jobseeker Work Experience

_This route is intended for use by a jobseeker to delete a Work Experience from their profile_

**Endpoint**: `/api/jobseekers/work-experience/remove/<workId>`

**Method**: `DELETE`

##### Sample Response

**DTO**: result property is `WorkExperience` type generated by PrismaClient from schema.prisma

```json
{
  "success": true,
  "result": {
    "workId": "ddf90cad-5273-4651-aef3-340ea8494335",
    "jobseekerId": "48586cd0-74ba-4da0-9bb2-2862a5c7ca5b",
    "techAreaId": "4c376b09-38e2-4278-b70b-975837c43fe5",
    "company": "CFA",
    "isInternship": true,
    "jobTitle": "intern",
    "isCurrentJob": false,
    "startDate": "2022-01-01T00:00:00.000Z",
    "endDate": "2022-03-25T00:00:00.000Z",
    "responsibilities": "Microsoft Dynamics Plugins for admin workflow"
  }
}
```

---

### Showcase Page

---

#### Read Showcase page

_This route is meant to be used with the `/edit-profile/jobseeker/showcase` page for initial load of data, if any._

**Endpoint**: `/api/jobseekers/account/showcase/get/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property is type `JsShowcaseDTO`.

```json
{
  "success": true,
  "result": {
    "userId": "71099f10-054e-4027-9237-ef2da5b071ff",
    "skills": [
      {
        "skill_id": "2e560cd6-2560-4aca-b47b-aeebafc0bdd7",
        "skill_name": "Samba (Software)",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS4407R6K7SXDL4JTSW9"
      },
      {
        "skill_id": "48925f92-982a-45f4-8183-613fb3c257ab",
        "skill_name": "Variable-Length Subnet Masking (VLSM)",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS441WD6BX1NJ03KKWT1"
      },
      {
        "skill_id": "67e0630b-0806-4d26-a2f1-87ff57d77368",
        "skill_name": "Artificial Intelligence Markup Language (AIML)",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS120C16DHL5K6SSZX7F"
      },
      {
        "skill_id": "8480e593-d0d3-4bbe-8a5f-104221485ec7",
        "skill_name": "Spring AOP",
        "skill_info_url": "https://lightcast.io/open-skills/skills/ESD850EECFAA1B3058FD"
      },
      {
        "skill_id": "9abeb859-9e74-4378-8cfa-5fb870b912c1",
        "skill_name": "Vim (Text Editor)",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS124K86RDS814LF5MC9"
      }
    ],
    "portfolioUrl": "https://lost-clone.biz/",
    "portfolioPassword": null,
    "video_url": "https://blaring-existence.info/"
  }
}
```

---

#### Upsert Showcase Page

_This route is meant to be used with the `/edit-profile/jobseeker/showcase` page for updating or creating data._

**Endpoint**: `/api/jobseekers/account/showcase/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `JsShowcaseDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "portfolioUrl": "https://lost-clone.biz/",
  "portfolioPassword": "drowssap",
  "video_url": "https://my-video.url",
  "skills": [
    {
      "skill_id": "356e0040-8400-49a0-b772-6f6475776612",
      "skill_name": "JavaScript",
      "skill_info_url": "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language"
    },
    {
      "skill_id": "38943cce-679d-408f-9fb1-6d054012e54f",
      "skill_name": ".NET Assemblies",
      "skill_info_url": "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X"
    }
  ]
}
```

##### Sample Response

**DTO**: result property is type `JsShowcaseDTO`.

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "portfolioUrl": "https://lost-clone.biz/",
    "portfolioPassword": "drowssap",
    "video_url": "https://my-video.url",
    "skills": [
      {
        "skill_id": "356e0040-8400-49a0-b772-6f6475776612",
        "skill_name": "JavaScript",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language"
      },
      {
        "skill_id": "38943cce-679d-408f-9fb1-6d054012e54f",
        "skill_name": ".NET Assemblies",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X"
      }
    ]
  }
}
```

---

#### Read Skills

_Intended for use where showing project skills in addition to the top 5 skills is desired. Any duplicate skills between
topSkills and OtherSkills are removed from the OtherSkills Array._

**Endpoint**: `/api/skills/get/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property is of type `{topSkills: SkillDTO[], otherSkills: SkillDTO[]}`.

```json
{
  "success": true,
  "result": {
    "topSkills": [
      {
        "skill_id": "0e52f663-173f-4eea-acb6-8485155a1d98",
        "skill_name": "Desktop Management Interface",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS7G2PN5YHRMM2XMFK68"
      },
      {
        "skill_id": "49172554-720b-4860-88e8-5532dd04c27d",
        "skill_name": "Markup Languages",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS1233M6Q271L5ZNBP86"
      }
    ],
    "otherSkills": [
      {
        "skill_id": "0141892a-3b07-403c-9763-0c5cefc36bae",
        "skill_name": "Active Directory",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS1205G5ZKS8ZZWVPM9Y"
      },
      {
        "skill_id": "6eda964a-a65d-4544-abe1-6382cd3ea8fe",
        "skill_name": "Geoprocessing",
        "skill_info_url": "https://lightcast.io/open-skills/skills/KS124B66RYT8PC9B4WPQ"
      }
    ]
  }
}
```

---

#### Upsert Jobseeker Skills

_Used to push jobseeker selected skills into the database_

**Endpoint**: `/api/skills/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `none`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "skillIds": [
    "356e0040-8400-49a0-b772-6f6475776612",
    "38943cce-679d-408f-9fb1-6d054012e54f"
  ]
}
```

##### Sample Response

**DTO**: Result is property type `SKillDTO[]`

```json
{
  "success": true,
  "result": [
    {
      "skill_id": "356e0040-8400-49a0-b772-6f6475776612",
      "skill_name": "JavaScript",
      "skill_info_url": "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language"
    },
    {
      "skill_id": "38943cce-679d-408f-9fb1-6d054012e54f",
      "skill_name": ".NET Assemblies",
      "skill_info_url": "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X"
    }
  ]
}
```

---

#### Delete Jobseeker Skill

_This route is intended for use with the `/edit-profile/jobseeker/showcase` page. It can be used anywhere skills
needs unassociated with a jobseeker._

**Endpoint**: `/api/skills/remove`

**Method**: `DELETE`

##### Sample Request

**DTO**: `none`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "skillIds": [
    "356e0040-8400-49a0-b772-6f6475776612",
    "38943cce-679d-408f-9fb1-6d054012e54f"
  ]
}
```

##### Sample Response

**DTO**: result is property type `SKillDTO[]`

```json
{
  "success": true,
  "result": [
    {
      "skill_id": "356e0040-8400-49a0-b772-6f6475776612",
      "skill_name": "JavaScript",
      "skill_info_url": "https://lightcast.io/open-skills/skills/KS1200771D9CR9LB4MWW/javascript-programming-language"
    },
    {
      "skill_id": "38943cce-679d-408f-9fb1-6d054012e54f",
      "skill_name": ".NET Assemblies",
      "skill_info_url": "https://lightcast.io/open-skills/skills/KS126XS6CQCFGC3NG79X"
    }
  ]
}
```

---

#### Jobseeker Video Delete

_This route is meant to be used with the `/edit-profile/jobseeker/showcase` page. It will set the jobseekers.video_url
property to null and mark it for
deletion in blob storage._

> Blob storage isn't available yet. Plan on implementing as soon as we have access.

**Endpoint**: `/api/jobseekers/video/remove/<userId>`

**Method**: `PATCH`

##### Sample Response

**DTO**: `{jobseekerId: string, videoUrl?: string | null}`

```json
{
  "success": true,
  "result": {
    "jobseekerId": "8d1026fa-b723-4b55-95d3-7d8a7f40d9b0",
    "videoUrl": null
  }
}
```

---

### Preferences Page

---

#### Read Preferences

_This route is intended to load the `/edit-profile/jobseeker/preferences` page with preexisting data, if any_

**Endpoint**: `/api/jobseekers/account/preferences/get/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property is of type `JsPreferencesDTO & {targetedPathway?: string | null}`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "targetedPathwayId": "79608104-d50e-4d0f-b541-2a9de7bc0f89",
    "targetedPathway": "Software Development",
    "preferredEmploymentType": "Full-time"
  }
}
```

---

#### Upsert Jobseeker Preferences

_This is intended for use updating or creating Jobseeker preferences on the `/edit-profile/jobseeker/preferences`
page_

**Endpoint**: `/api/jobseekers/account/preferences/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `JsPreferencesDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "targetedPathwayId": "79608104-d50e-4d0f-b541-2a9de7bc0f89",
  "preferredEmploymentType": "Full-time"
}
```

##### Sample Response

**DTO**: result property is of type `JsPreferencesDTO & {targetedPathway?: string | null}`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "targetedPathwayId": "79608104-d50e-4d0f-b541-2a9de7bc0f89",
    "targetedPathway": "Software Development",
    "preferredEmploymentType": "Full-time"
  }
}
```

---

### Voluntary Disclosures Page

---

#### Read Jobseeker Disclosures

_Intended to load Jobseeker disclosures data in `/edit-profile/jobseeker/disclosures` page, if any._

**Endpoint**: `/api/jobseekers/account/disclosures/get/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: `JsDisclosuresDTO`

```json
{
  "success": true,
  "result": {
    "jobseekerId": "96682e87-4940-411f-a09c-be7d45d118c8",
    "gender": "male",
    "race": "caucasian",
    "hasReadTerms": true,
    "isVeteran": "No",
    "hasDisability": "Prefer not to say"
  }
}
```

---

#### Upsert Disclosures

_Intended to be used with the `/edit-profile/jobseeker/disclosures` page to update or create disclosure data._

**Endpoint**: `/api/jobseekers/account/disclosures/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `JsDisclosuresPOSTDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "gender": "male",
  "race": "caucasian",
  "hasReadTerms": true,
  "isVeteran": "No",
  "hasDisability": "Prefer not to say"
}
```

##### Sample Response

**DTO**: `JsDisclosuresDTO`

```json
{
  "success": true,
  "result": {
    "jobseekerId": "96682e87-4940-411f-a09c-be7d45d118c8",
    "gender": "male",
    "race": "caucasian",
    "hasReadTerms": true,
    "isVeteran": "No",
    "hasDisability": "Prefer not to say"
  }
}
```

---

### Employer Routes

---

### Employer Account Creation

---

#### Upsert Employer Personal Information Page

_This route is used to upsert information from the employer account creation personal information page. This _

**Endpoint**: `api/employers/account/personal-info/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `PostEmployerPersonalDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "firstName": "Inita",
  "lastName": "Talent",
  "birthDate": "1990-12-08",
  "email": "inita@employer.com",
  "phoneCountryCode": "+44-1624",
  "phone": "123-456",
  "gender": "female",
  "race": "asian",
  "photoUrl": "https://blobName.myphoto-123.png"
}
```

##### Sample Response

**DTO**: result property is type `ReadEmployerPersonalDTO`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "firstName": "Inita",
    "lastName": "Talent",
    "birthDate": "1990-12-08T00:00:00.000Z",
    "email": "inita@employer.com",
    "phoneCountryCode": "44",
    "phone": "+441624123456",
    "gender": "female",
    "race": "asian",
    "photoUrl": "https://blobName.myphoto-123.png"
  }
}
```

---

#### Read Employer Personal Information Page

_This route is used for the initial load of data for Account Page: Employer Personal Information._

**Endpoint**: `/api/employers/account/personal-info/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property is type `ReadEmployerPersonalDTO`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "firstName": "Inita",
    "lastName": "Talent",
    "birthDate": "1990-12-08T00:00:00.000Z",
    "email": "inita@employer.com",
    "phoneCountryCode": "44",
    "phone": "+441624123777",
    "gender": "female",
    "race": "asian",
    "photoUrl": "https://blobName.myphoto-123.png"
  }
}
```

---

#### Upsert Employer Professional Information Page

_This route is used for the initial load of data for Account Page: Employer Professional Information. There needs to be
a drop-down for an employer to select companies' address_

**Endpoint**: `/api/employers/account/professional-info/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `PostEmployerWorkDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "currentJobTitle": "Full-stack Developer",
  "linkedInUrl": "https://www.linkedin.com/in/theEmployer/",
  "workAddressId": "8c08d31f-9e1f-4172-b195-66e528e39fd6"
}
```

##### Sample Response

**DTO**: result property is type `ReadEmployerWorkDTO & CompanyInfoSummaryDTO`

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "employerId": "57d46b6e-ace6-45c5-969c-79fb71beef24",
    "currentJobTitle": "Full-stack Developer",
    "linkedInUrl": "https://www.linkedin.com/in/theEmployer/",
    "companyId": "10a34e0f-97af-40c8-8258-d460dd4d3a91",
    "companyName": "Gulgowski - Mohr",
    "isVerifiedEmployee": false,
    "companyAddress": {
      "addressId": "97da86f2-e596-4370-9a72-d4ec354580c0",
      "city": "Jackson",
      "state": "WA",
      "zipCode": "99350"
    }
  }
}
```

---

#### Read Employer Professional Information Page

_This route is used for the initial load of data for Account Page: Employer Professional Information._

**Endpoint**: `api/employers/account/professional-info/<userId>`

**Method**: `GET`

##### Sample Response

**DTO**: ``

```json
{
  "success": true,
  "result": {
    "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
    "employerId": "57d46b6e-ace6-45c5-969c-79fb71beef24",
    "currentJobTitle": "Full-stack Developer",
    "linkedInUrl": "https://www.linkedin.com/in/theEmployer/",
    "companyId": "10a34e0f-97af-40c8-8258-d460dd4d3a91",
    "companyName": "Gulgowski - Mohr",
    "isVerifiedEmployee": false,
    "companyAddress": {
      "addressId": "97da86f2-e596-4370-9a72-d4ec354580c0",
      "city": "Jackson",
      "state": "WA",
      "zipCode": "99350"
    }
  }
}
```

---

#### Upsert Employer Company Information Page

_This route is used for upserting employer data for Account Page: Employer Company Information._

**Endpoint**: `/api/employers/account/company-info/upsert`

**Method**: `POST`

##### Sample Request

**DTO**: `PostCompanyInfoDTO`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "companyId": "10a34e0f-97af-40c8-8258-d460dd4d3a91",
  "industrySectorId": "60829f24-fbaf-46aa-9ad7-1f4810de1069",
  "companyName": "Gulgowski - Mohr",
  "companyAddresses": [
    {
      "city": "Thousand Oaks",
      "state": "Washington",
      "zipCode": "98092",
      "county": "Pierce"
    }
  ],
  "logoUrl": "https://monthly-sentence.org",
  "aboutUs": "Adstringo triumphus vado dapifer verumtamen sumptus uberrime volva suasoria socius. Tantum vulariter socius vetus sto socius.",
  "companyEmail": "Sophie.McClure65@yahoo.com",
  "yearFounded": "1995",
  "websiteUrl": "https://even-policy.biz/",
  "videoUrl": "https://stylish-pursuit.com",
  "phoneCountryCode": "+1",
  "companyPhone": "2065555555",
  "mission": "Hire everyone!",
  "vision": "Amita clarus tumultus theca adimpleo amoveo amet statim adipisci. Amita concedo viscus tener dicta auditor desino deduco sonitus. Cinis blandior velum agnitio.",
  "employeeCount": "249",
  "estimatedAnnualHires": "10"
}
```

##### Sample Response

**DTO**: result property is of type `ReadCompanyInfoDTO`

```json
{
  "success": true,
  "result": {
    "companyId": "10a34e0f-97af-40c8-8258-d460dd4d3a91",
    "industrySectorId": "60829f24-fbaf-46aa-9ad7-1f4810de1069",
    "industrySectorTitle": "Retail",
    "companyName": "Gulgowski - Mohr",
    "companyAddresses": [
      {
        "addressId": "97da86f2-e596-4370-9a72-d4ec354580c0",
        "state": "WA",
        "city": "Jackson",
        "zipCode": "99350",
        "county": "Benton"
      },
      {
        "addressId": "83105c24-f72c-4707-924c-e2f96923a2d9",
        "state": "Washington",
        "city": "Thousand Oaks",
        "zipCode": "98092",
        "county": "Pierce"
      },
      {
        "addressId": "6abc28c5-7208-4a75-ae31-132f14f16952",
        "state": "Washington",
        "city": "Sequim",
        "zipCode": "98382",
        "county": "Clallam"
      }
    ],
    "logoUrl": "https://monthly-sentence.org",
    "aboutUs": "Adstringo triumphus vado dapifer verumtamen sumptus uberrime volva suasoria socius. Tantum vulariter socius vetus sto socius.",
    "companyEmail": "Sophie.McClure65@yahoo.com",
    "yearFounded": "1995",
    "websiteUrl": "https://even-policy.biz/",
    "videoUrl": "https://stylish-pursuit.com",
    "phoneCountryCode": "1",
    "companyPhone": "+12065555555",
    "mission": "Hire everyone!",
    "vision": "Amita clarus tumultus theca adimpleo amoveo amet statim adipisci. Amita concedo viscus tener dicta auditor desino deduco sonitus. Cinis blandior velum agnitio.",
    "employeeCount": "249",
    "estimatedAnnualHires": "10",
    "isApproved": false
  }
}
```

---

#### Get Company Locations By ID

_This is used to get the locations for a specific company_

**Endpoint**: `/api/employers/companies/locations/<companyId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property is of type `ReadAddressDTO[]`

```json
{
  "success": true,
  "result": [
    {
      "addressId": "c633d591-8312-44ad-85d1-7bd6f97d0cc5",
      "city": "Clarksville",
      "state": "WA",
      "zipCode": "99347",
      "county": "Garfield"
    },
    {
      "addressId": "8c08d31f-9e1f-4172-b195-66e528e39fd6",
      "city": "Thousand Oaks",
      "state": "Washington",
      "zipCode": "98092",
      "county": "Pierce"
    }
  ]
}
```

---

#### Read Employer Company Information Page

_This route is used for the initial load of data for Account Page: Employer Company Information._

**Endpoint**: `/api/employers/account/company-info/<companyId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property is of type `ReadCompanyInfoDTO`

```json
{
  "success": true,
  "result": {
    "companyId": "10a34e0f-97af-40c8-8258-d460dd4d3a91",
    "industrySectorId": "60829f24-fbaf-46aa-9ad7-1f4810de1069",
    "industrySectorTitle": "Retail",
    "companyName": "Gulgowski - Mohr",
    "logoUrl": "https://monthly-sentence.org",
    "aboutUs": "Adstringo triumphus vado dapifer verumtamen sumptus uberrime volva suasoria socius. Tantum vulariter socius vetus sto socius.",
    "companyEmail": "Sophie.McClure65@yahoo.com",
    "yearFounded": "1995",
    "websiteUrl": "https://even-policy.biz/",
    "videoUrl": "https://stylish-pursuit.com",
    "phoneCountryCode": "1",
    "companyPhone": "+12065555555",
    "mission": "Hire everyone!",
    "vision": "Amita clarus tumultus theca adimpleo amoveo amet statim adipisci. Amita concedo viscus tener dicta auditor desino deduco sonitus. Cinis blandior velum agnitio.",
    "employeeCount": "249",
    "estimatedAnnualHires": "10",
    "isApproved": false,
    "companyAddresses": [
      {
        "addressId": "97da86f2-e596-4370-9a72-d4ec354580c0",
        "state": "WA",
        "city": "Jackson",
        "zipCode": "99350",
        "county": "Benton"
      },
      {
        "addressId": "83105c24-f72c-4707-924c-e2f96923a2d9",
        "state": "Washington",
        "city": "Thousand Oaks",
        "zipCode": "98092",
        "county": "Pierce"
      },
      {
        "addressId": "6abc28c5-7208-4a75-ae31-132f14f16952",
        "state": "Washington",
        "city": "Sequim",
        "zipCode": "98382",
        "county": "Clallam"
      }
    ]
  }
}
```

---

#### Update Employer Work Address

_This is intended for an employer to choose their work location for companies that have more than one location_

**Endpoint**: `/api/employers/account/work-address/update`

**Method**: `POST`

##### Sample Request

**DTO**: `none`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "companyAddressId": "d12383f7-0526-4682-8b32-016654bac9ed"
}
```

##### Sample Response

**DTO**: result property is of type `ReadEmployerWorkDTO & CompanyInfoSummaryDTO`

```json
{
  "success": true,
  "result": {
    "employerId": "2babec5f-3bd0-4356-9d82-34f13874e577",
    "currentJobTitle": "Full-stack Developer",
    "linkedInUrl": "https://www.linkedin.com/in/theEmployer/",
    "companyId": "00b5c928-e865-433f-bd6c-10236e46846d",
    "companyName": "Gulgowski - Mohr",
    "isVerifiedEmployee": false,
    "companyAddress": {
      "addressId": "d12383f7-0526-4682-8b32-016654bac9ed",
      "city": "Thousand Oaks",
      "state": "Washington",
      "zipCode": "98092"
    }
  }
}
```

---

#### Update Employer Work Address

_This route is intended for use by the employer to update their work location_

**Endpoint**: `api/employers/work-location/update`

**Method**: `PATCH`

##### Sample Request

**DTO**: `none`

```json
{
  "userId": "ae80e273-2975-4703-a894-f3c1e01428fd",
  "companyAddressId": "97da86f2-e596-4370-9a72-d4ec354580c0"
}
```

##### Sample Response

**DTO**: result property is of type `ReadEmployerWorkDTO & CompanyInfoSummaryDTO`

```json
{
  "success": true,
  "result": {
    "employerId": "57d46b6e-ace6-45c5-969c-79fb71beef24",
    "currentJobTitle": "Full-stack Developer",
    "linkedInUrl": "https://www.linkedin.com/in/theEmployer/",
    "companyId": "10a34e0f-97af-40c8-8258-d460dd4d3a91",
    "companyName": "Gulgowski - Mohr",
    "isVerifiedEmployee": false,
    "companyAddress": {
      "addressId": "97da86f2-e596-4370-9a72-d4ec354580c0",
      "city": "Jackson",
      "state": "WA",
      "zipCode": "99350"
    }
  }
}
```

---

#### Get Company Locations by Company ID

_Intended to display company locations for company page and for the Employer to choose their work location._

**Endpoint**: `api/companies/locations/get/<companyId>`

**Method**: `GET`

##### Sample Response

**DTO**: result property is of type `ReadAddressDTO[]`

```json
{
  "success": true,
  "result": [
    {
      "addressId": "97da86f2-e596-4370-9a72-d4ec354580c0",
      "city": "Jackson",
      "state": "WA",
      "zipCode": "99350",
      "county": "Benton"
    },
    {
      "addressId": "22ac8110-4b0b-4ee6-ba94-8c4311ad0401",
      "city": "Thousand Oaks",
      "state": "Washington",
      "zipCode": "98092",
      "county": "Pierce"
    },
    {
      "addressId": "6abc28c5-7208-4a75-ae31-132f14f16952",
      "city": "Sequim",
      "state": "Washington",
      "zipCode": "98382",
      "county": "Clallam"
    }
  ]
}
```

---

#### Add Company Location

_Intended for an APPROVED employer to add a work location. There should be one unique entry per zip code._

**Endpoint**: `api/companies/locations/add`

**Method**: `POST`

##### Sample Request

**DTO**: `PostAddressDTO & {companyId: string}`

```json
{
  "companyId": "10a34e0f-97af-40c8-8258-d460dd4d3a91",
  "city": "Thousand Oaks",
  "state": "Washington",
  "zipCode": "98092",
  "county": "Pierce"
}
```

##### Sample Response

**DTO**: result property is type `ReadAddressDTO`

```json
{
  "success": true,
  "result": {
    "addressId": "83105c24-f72c-4707-924c-e2f96923a2d9",
    "city": "Thousand Oaks",
    "state": "Washington",
    "zipCode": "98092",
    "county": "Pierce"
  }
}
```

---

#### Delete Company Location by locationId

_This is intended for an APPROVED employer to remove company locations._

**Endpoint**: `api/companies/locations/remove/<locationId>`

**Method**: `DELETE`

##### Sample Response

**DTO**: result property is type `ReadAddressDTO`

```json
{
  "success": true,
  "result": {
    "addressId": "22ac8110-4b0b-4ee6-ba94-8c4311ad0401",
    "city": "Thousand Oaks",
    "state": "Washington",
    "zipCode": "98092",
    "county": "Pierce"
  }
}
```

---
