# Computing for All - _Tech Talent Showcase_

This repository contains the source code for the Washington Tech Workforce Coalition Tech Talent Showcase website, built with Next.js and Prisma ORM, styled with TailwindCSS. This application helps match employers with jobseekers in the tech industry.

## Reference Designs

- [Jobseeker-UX](https://www.figma.com/design/g54drsZOvLMZNvrAIrpJkH/MVP-R2-09%2F10?node-id=20-13140&node-type=SECTION&t=fBQRgvGKBt9RLMPO-0)
- [Employer-Flow--MVP](https://www.figma.com/design/g54drsZOvLMZNvrAIrpJkH/MVP-R2-09%2F10?node-id=1-285&node-type=CANVAS&t=1e2jUf2kdpkjDTUi-0)

## Prerequisites

- Node.js >= 18.17.0
- npm
- MSSQL Server (optional)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/runefather/frontend-cfa.git
cd frontend-cfa
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Set Up Environment Variables

If you are creating your own local MSSQL server, we recommend using Docker Compose. Follow our [instructions for setting up MSSQL](setup-MSSQL.md).

Otherwise, if you're just working on the frontend, you can use our shared cloud dev MSSQL server! Create a `.env` file in the root directory of your project and copy the below text there. Add your generated Base64 Auth Secret and save!

```env
# Dev Test Azure DB
DATABASE_URL="sqlserver://cfa-reactdb.database.windows.net;database=dev;user=talentfinder;password=CFA2024@Next.js;encrypt=true;trustServerCertificate=true"

# Azure Services - Blob Storage
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=careerservicesstorage;AccountKey=Y81x4YjIyS2W2fhIR6sW/05Lom1hTgyhBhYAvDFKcxf7GYE7Fxo3D+JfMRoHShpT5XAKbi4Vjuuc+AStdQgGjA==;EndpointSuffix=core.windows.net"
AZURE_STORAGE_ACCOUNT_KEY="Y81x4YjIyS2W2fhIR6sW/05Lom1hTgyhBhYAvDFKcxf7GYE7Fxo3D+JfMRoHShpT5XAKbi4Vjuuc+AStdQgGjA=="
AZURE_STORAGE_NAME="careerservicesstorage"

# ESS Services  ######## TODO use application user consolidate with Azure Services, if possible ########
NEXT_PUBLIC_TENANT_ID="a3c7a257-40f2-43a9-9373-8bb5fc6862f7"
NEXT_PUBLIC_CLIENT_ID="dfc4e746-44b7-420b-8463-ad6011728b8d"
NEXT_PUBLIC_BASE_URL="https://cfahelpdesksandbox.api.crm.dynamics.com/api/data/v9.1"
NEXT_PUBLIC_TOKEN_SCOPE="https://cfahelpdesksandbox.crm.dynamics.com/.default"

# Shared Auth Secrets
AUTH_GITHUB_ID=Ov23li9hwTQuo1iWqrNH
AUTH_GITHUB_SECRET=3be8d9d590b4b30df7df1d9513eb4280e605f6fa
GOOGLE_CLIENT_ID="896719689092-a8qllfgn2nir2uk1t3p4jf6d1tb5bsnn.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET=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

# Personal Auth Secret - generate by running the following command: openssl rand -base64 32
AUTH_SECRET=<your generated base64 auth secret>
```

If there are new changes that need to be applied to the SQL server, you can run the following commands to reset, update, and reseed everything: `npx prisma migrate reset`, then `npm run seed`.

If you're running into unexpected issues, someone else probably changed something. Terminate your `npm run dev` and then run `npx prisma generate`.

### 4. Run the Development Server

Start the development server:

```bash
npm run dev
```

Open your browser and navigate to [http://localhost:3000](http://localhost:3000) to see the application in action!

---

## Tutorials and Documentation

- [Branching Strategy](branch-strategy.md)
- [Set up local MSSQL Server](setup-MSSQL.md)
- [Changing the DB schema](prisma-workflow.md)
- [API Routes](API-routes.md)
- [CSS Utilities & Styling Guide](styling-guide.md)

## Available `npm run` Scripts

- `build`: Builds the application for production.
- `dev`: Runs the application in development mode.
- `prettier`: Formats the code using Prettier.
- `prettier:check`: Checks if the code is formatted according to Prettier.
- `start`: Starts the application in production mode.
- `seed`: Seeds the database with initial data.
- `lint`: Runs ESLint to check for code issues.

## Technologies Used

- **Next.js**: React framework for server-side rendering. [Next.js Documentation](https://nextjs.org/docs)
- **Prisma**: Database ORM for TypeScript and Node.js. [Prisma Documentation](https://www.prisma.io/docs)
- **TailwindCSS**: Utility-first CSS framework. [TailwindCSS Documentation](https://tailwindcss.com/docs)
- **Auth.js**: Authentication library for Next.js. [Auth.js Documentation](https://authjs.dev/docs)
- **MSSQL**: Microsoft SQL Server database. [MSSQL Documentation](https://docs.microsoft.com/en-us/sql/sql-server)

## License

This project is licensed under the MIT License. See the LICENSE file for details.
