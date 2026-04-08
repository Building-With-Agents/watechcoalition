## 8. Prisma ORM Workflow

#### 8.1. Making changes to the Database with prisma/schema.prisma file

There are two main schema migration patterns. 1) **Model/Entity-first migration** 2) **Database-first migration**. We
are using the **Model/Entity-first migration pattern** with this pattern, you define the structure of the database
schema with code and then use a migration tool to generate the SQL.
Gain further insights in the
Prisma/docs [Mental model](https://www.prisma.io/docs/orm/prisma-migrate/understanding-prisma-migrate/mental-model).

> These changes to the db schema are defined in the prisma/schema.prisma file

#### 8.2. After making changes to the schema.prisma file run the following CLI command:

```bash
npx prisma migrate dev --name "<brief-description-of-change>"
```

Running `prisma migrate dev` stores the changes in two separate locations:

1. In code in the prisma/migrations directory. Any migrations should be saved and stored to the repository.
2. In the \_prisma_migrations table of the database

This will create a folder in the in prisma/migrations directory containing a migration.sql file. The name of the folder
is prefixed with the timestamp and appended with the name given when running `prisma migrate dev`. The migration.sql
file contains the SQL commands that are applied to the database. See more in the
Prisma/docs [About migration histories](https://www.prisma.io/docs/orm/prisma-migrate/understanding-prisma-migrate/migration-histories)

> There are occasions when the migrations do not work correctly and conflicts need resolved. If making changes
> manually to the database it is important to make sure any modifications to the `migration.sql` file are also applied
> to the \_prisma_migrations table record in the database and vice versa. Learn more in Prisma
> docs [Customizing Migrations](https://www.prisma.io/docs/orm/prisma-migrate/workflows/customizing-migrations)

#### 8.3. To ensure prisma migrations are applied correctly you can run the following command.

```bash
npx prisma migrate reset
```

This will drop all data from the database and apply all migrations in the prisma/migrations folder. After applying the
migrations the PrismaClient is updated. That is immediately after reset the CLI command `npx prisma generate` is
invoked.

_Note. If the development server is running the PrismaClient will not be updated. Stop the development environment and
run `npx prisma generate` to update the PrismaClient manually._

```bash
npx prisma generate
```

Learn more about the Prisma Client and `npx prisma generate` at
Prisma/docs [Accessing your database with Prisma Client](https://www.prisma.io/docs/orm/overview/introduction/what-is-prisma#accessing-your-database-with-prisma-client)
