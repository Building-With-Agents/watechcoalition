import { getAllUsers } from "@/app/lib/user";
import * as React from "react";
import EditUsersTable from "@/app/ui/components/admin/EditUsersTable";

export default async function Page() {
  const users = await getAllUsers();
  return (
    <main>
      <EditUsersTable users={users} />
    </main>
  );
}
