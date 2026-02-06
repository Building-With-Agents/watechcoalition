# Training exercises (setup + golden code + where to see failures)

This repo uses a **training branch** to create intentionally broken code paths for interns to fix.

- On **`restore/db-in-use-dev`**: everything should be **working**.
- On **`training/exercises-v1`**: specific sections are **intentionally broken**, with inline comments pointing back to this doc.

## Clone + setup (local dev)

### Prereqs

- Node.js (use the version expected by the repo)
- Docker Desktop
- Azure OpenAI env vars (see `.env.local`)

### Clone

```bash
git clone <REPO_URL>
cd frontend-cfa
```

### Install dependencies

```bash
npm ci
```

### Configure env vars

1. Copy `.env.example` → `.env.local`
2. Fill in these variables (both chat + embeddings are required):
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_API_KEY`
   - `AZURE_OPENAI_API_VERSION`
   - `AZURE_OPENAI_DEPLOYMENT_NAME`
   - `AZURE_OPENAI_EMBEDDING_ENDPOINT`
   - `AZURE_OPENAI_EMBEDDING_API_KEY`
   - `AZURE_OPENAI_EMBEDDING_API_VERSION`
   - `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME`

### Start Docker SQL Server

- Use `docker-compose.yml` (and see `setup-MSSQL.md` / `docs/DOCKER_SQL_SERVER_SETUP.md` if you get stuck).

```bash
docker compose up -d
```

### Create schema + populate the DB

Recommended (anonymized fixtures):

```bash
npx prisma db push
npx prisma generate
npm run db:seed:anonymized
```

Optional (if you need skill embeddings populated in `skills.embedding`):

- As an admin, visit **`/admin/dashboard/generate-embeddings`** and click **Generate**.

### Start the app

```bash
npm run dev
```

## How interns use this

1. Check out `training/exercises-v1`.
2. Run the app.
3. Reproduce a failure using the **Where you see it** section for an exercise.
4. Fix the code at the referenced file/function by restoring the **golden code** below.
5. Verify using the listed verification steps.

---

## vector-search

### Exercise A: Vector search query is broken (metric + dimension)

### Where you see it in the website

- Go to **`/ess/<jobrole>`** as an approved employer.
- Expand **Employer Feedback Form**.
- In **Select Additional Skill**, type a skill name to trigger autocomplete.

This uses:

- UI: `app/ui/components/feedback-forms/EmployerFeedbackForm.tsx`
- API: `GET /api/skills/vsearch/[terms]`
- DB query: `app/lib/prisma.ts` → `vectorSearchSkills()`

### Symptom

- Skill autocomplete fails; network shows **500** from `GET /api/skills/vsearch/<terms>`.
- Server logs show a SQL error about **invalid distance metric** and/or **vector dimension mismatch**.

### Where to fix

- `app/lib/prisma.ts` → `vectorSearchSkills`

### Golden code (correct)

The query must use:

- metric: **`COSINE`**
- cast: **`VECTOR(1536)`**

```ts
VECTOR_DISTANCE('COSINE', embedding, CAST(${queryVectorJsonString} AS VECTOR(1536))) as distance
```

### What to change

- Ensure the metric string is exactly **`COSINE`**.
- Ensure the cast dimension is **`1536`** (must match the `skills.embedding` column).

### How to verify

- Repeat the ESS autocomplete flow above and confirm:
  - `GET /api/skills/vsearch/<terms>` returns **200**
  - Suggestions appear in the autocomplete dropdown

---

## vsearch-route

### Exercise B: vsearch route auth/response behavior is wrong

### Where you see it in the website

- Go to **`/ess/<jobrole>`** as an approved employer.
- Expand **Employer Feedback Form**.
- Use the **Select Additional Skill** autocomplete.

### Symptom

- You see **401** or **500** from `GET /api/skills/vsearch/<terms>` even when logged in as an employer.

### Where to fix

- `app/api/skills/vsearch/[terms]/route.ts` → `GET`

### Golden code (correct)

```ts
const session = await auth();
if (session) {
  const params = await props.params;
  const terms = decodeURIComponent(params.terms);
  const searchResults = await vectorSearchSkills(terms, 5);
  return Response.json(searchResults, { status: 200 });
}
return Response.json({ status: 401 });
```

### What to change

- Ensure authenticated requests return **200** and include the search results.

### How to verify

- Repeat the ESS autocomplete flow above and confirm `GET /api/skills/vsearch/<terms>` returns **200**.

---

## parse-text-route

### Exercise C: parse-text route (Azure OpenAI → skills) is broken

### Where you see it in the website

Pick either flow (both call the same API):

- **Career Prep**: go to **`/career-prep/generic-job-match`**, paste a job description, and run the flow that fetches skills/candidates.
- **Employer Dashboard**: go to **`/services/employers/dashboard`** and click **New Job**; entering a description triggers background skill parsing when you advance steps.

This uses:

- API: `POST /api/skills/parse-text`

### Symptom

- Career Prep page shows “Skill parsing failed …”
- Employer New Job flow logs errors in console
- Network shows **502** or **500** from `POST /api/skills/parse-text`

### Where to fix

- `app/api/skills/parse-text/route.ts` → `POST`

### Golden code (correct)

Key behaviors the route must preserve:

- Call `parseTextForSkills(text)`
- `JSON.parse(raw)` safely
- Return an array of matched `SkillDTO` via `vectorSearchSkills`

```ts
raw = await parseTextForSkills(text);
// ... handle empty response ...
parseResult = JSON.parse(raw);
const parsedSkills = parseResult.skills || [];
// ... for each parsed skill, vectorSearchSkills(skillName, 1) ...
return NextResponse.json(topSkills);
```

### How to verify

- On the Career Prep page, the skills list populates and `POST /api/skills/parse-text` returns **200** with a JSON array.

---

## admin-embeddings

### Exercise D: admin skill embeddings generation is broken

### Where you see it in the website

- Go to **`/admin/dashboard/generate-embeddings`** as an admin.
- Click **Generate**.

This uses:

- API: `POST /api/admin/generate-skill-embeddings`
- Logic: `app/lib/admin/skill.ts` → `generateAllSkillEmbeddings()` → `generateAndStoreEmbeddings()`

### Symptom

- The page alerts “Failed to create All skill embeddings”, or the API returns **500**.

### Where to fix

- `app/lib/admin/skill.ts` → `generateAndStoreEmbeddings`

### Golden code (correct)

Key behaviors that must be correct:

- Use the embeddings deployment env var: `AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME`
- Store embeddings cast to `VECTOR(1536)`

```ts
const resp = await client.embeddings.create({
  model: process.env.AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME!,
  input: batchNames,
  dimensions: 1536,
});

updateOps.push(
  prisma.$executeRaw`UPDATE skills SET embedding = CAST(${embeddingString} AS VECTOR(1536)) WHERE skill_id = ${skillId}`,
);
```

### How to verify

- Re-run the admin page flow and confirm the request succeeds and alerts success.
