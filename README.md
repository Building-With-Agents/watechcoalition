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
git clone https://github.com/Building-With-Agents/watechcoalition.git
cd watechcoalition
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Set Up Environment Variables

We recommend using Docker Compose to run SQL Server locally. Follow our [instructions for setting up MSSQL](setup-MSSQL.md) to configure your local database and environment variables.

Create a `.env` file in the root directory of your project with the required configuration. See `setup-MSSQL.md` for the complete environment variable template.

**Note**: Generate your Base64 Auth Secret by running: `openssl rand -base64 32`

If there are new changes that need to be applied to the SQL server, you can run the following commands to reset, update, and reseed everything: `npx prisma migrate reset`, then `npm run db:seed:anonymized`.

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
- `db:seed:anonymized`: Seeds the database with anonymized JSON fixtures from `prisma/mock-data/` (recommended for local dev).
- `seed`: Seeds the database with synthetic/faker-generated data (does not use `prisma/mock-data/`).
- `lint`: Runs ESLint to check for code issues.

## Technologies Used

- **Next.js**: React framework for server-side rendering. [Next.js Documentation](https://nextjs.org/docs)
- **Prisma**: Database ORM for TypeScript and Node.js. [Prisma Documentation](https://www.prisma.io/docs)
- **TailwindCSS**: Utility-first CSS framework. [TailwindCSS Documentation](https://tailwindcss.com/docs)
- **Auth.js**: Authentication library for Next.js. [Auth.js Documentation](https://authjs.dev/docs)
- **MSSQL**: Microsoft SQL Server database. [MSSQL Documentation](https://docs.microsoft.com/en-us/sql/sql-server)

## License

This project is licensed under the MIT License. See the LICENSE file for details.
