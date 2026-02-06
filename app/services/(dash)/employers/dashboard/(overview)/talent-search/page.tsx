import TalentSearch from "@/app/ui/components/TalentSearch";
import { CircularProgress } from "@mui/material";
import { Suspense } from "react";

export default async function Page() {
  return (
    <Suspense
      fallback={
        <div className="w-full h-full text-center">
          <CircularProgress />
        </div>
      }
    >
      <TalentSearch />
    </Suspense>
  );
}
