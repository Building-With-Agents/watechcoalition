import { unflagDeletion } from "@/app/lib/user";

export async function PATCH() {
  const response = await unflagDeletion(); // keep this
  // const response = await setPool('22D7FA11-78B0-4B36-8D8B-1021019008C5'); // here for testing purposes only.
  // const response = await deleteJobseeker('F0FAB330-D153-400A-BBB0-5C80752D18AA');
  return response;
}
