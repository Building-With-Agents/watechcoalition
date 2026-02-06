"use client";

import React, { useEffect, useState } from "react";
import Image from "next/image";
import Footer from "@/app/ui/Footer";
import SignupHeader from "@/app/ui/SignupHeader";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { Role } from "@/data/dtos/UserInfoDTO";
import PillButton from "@/app/ui/components/PillButton";

// interface Data {
//   userId: string;
//   role: string;
// }

export default function SignupPage() {
  const [choice, setChoice] = useState<Role>(Role.GUEST);
  const { data: session } = useSession();
  const router = useRouter();
  const checkIcon = (
    <Image
      src="/images/signup/check-mark.png"
      width={22}
      height={22}
      alt="Green checkmark"
      className="mr-2 inline"
    />
  );

  useEffect(() => {
    // Prefetch the potential pages when the component mounts
    router.prefetch("/signup/jobseeker");
    router.prefetch("/signup/employer");
  }, [router]);

  const handleSubmit = async () => {
    if (session) {
      if (choice === Role.JOBSEEKER) router.push(`/signup/jobseeker`);
      if (choice === Role.EMPLOYER) router.push(`/signup/employer`);
    }
  };

  return (
    <>
      <SignupHeader />
      <main className="flex flex-col gap-9 py-8">
        <h1 className="text-center text-4xl">Create account</h1>
        <fieldset className="flex flex-col items-center justify-center gap-8 sm-tablet:flex-row">
          <legend className="w-full pb-4 text-center">
            Select your role first
          </legend>
          <div>
            <input
              type="radio"
              name="account-role"
              id="account-employer"
              onClick={() => setChoice(Role.EMPLOYER)}
              className="peer hidden"
            />
            <label
              htmlFor="account-employer"
              className="relative block h-[180px] w-[200px] cursor-pointer rounded-md border-2 bg-white hover:bg-gray-100 peer-checked:border-primary-500 peer-checked:bg-primary-25"
            >
              <Image
                src="/images/signup/icon-employer.png"
                width={80}
                height={80}
                alt="Icon of a briefcase to represent employers."
                className="mx-auto py-6"
              />
              <p className="text-center">
                {choice === Role.EMPLOYER && checkIcon}An employer
              </p>
            </label>
          </div>
          <div>
            <input
              type="radio"
              name="account-role"
              id="account-jobseeker"
              onClick={() => setChoice(Role.JOBSEEKER)}
              className="peer hidden"
            />
            <label
              htmlFor="account-jobseeker"
              className="relative block h-[180px] w-[200px] cursor-pointer rounded-md border-2 bg-white hover:bg-gray-100 peer-checked:border-primary-500 peer-checked:bg-primary-25"
            >
              <Image
                src="/images/signup/icon-jobseeker.png"
                width={80}
                height={80}
                alt="Icon of a magnifying class to represent jobseekers."
                className="mx-auto py-6"
              />
              <p className="text-center">
                {choice === Role.JOBSEEKER && checkIcon}A job candidate
              </p>
            </label>
          </div>
        </fieldset>
        <PillButton
          disabled={choice === Role.GUEST}
          onClick={handleSubmit}
          variant="contained"
          sx={{
            marginInline: "auto",
            marginTop: "1rem",
            width: "fit-content",
            "&:disabled": {
              color: "#fff",
              bgcolor: "primary.main",
              opacity: 0.5,
            },
          }}
        >
          Continue
        </PillButton>
      </main>
      <footer className="mt-auto">
        <Footer />
      </footer>
    </>
  );
}
