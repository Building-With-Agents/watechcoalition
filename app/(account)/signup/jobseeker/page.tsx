"use client";

import SignupPrompt from "@/app/ui/components/SignupPrompt";
import Image from "next/image";
import Footer from "@/app/ui/Footer";
import SignupHeader from "@/app/ui/SignupHeader";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { useUpdateSession } from "@/app/lib/auth/useUpdateSession";
import { useSession } from "next-auth/react";
import { Role } from "@/data/dtos/UserInfoDTO";
import PillButton from "@/app/ui/components/PillButton";
import {
  Box,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormLabel,
  Link,
  Radio,
  RadioGroup,
} from "@mui/material";

const vectorImgSrc = "/images/signup/jobseeker-vector.png";

export default function JobseekerSignupFinishPage() {
  const [resident, setResident] = useState(false);
  const [checkboxState, setCheckboxState] = useState({
    jobNotifications: false,
    opportunities: false,
    termsAgree: false,
  });
  const { data: session } = useSession();
  const updateSessionProperties = useUpdateSession();
  const router = useRouter();

  const handleCheckboxChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, checked } = e.target;
    console.log(name);
    setCheckboxState((prevState) => ({
      ...prevState,
      [name]: checked,
    }));
  };

  return (
    <>
      <SignupHeader />

      <main className="mx-auto max-w-(--breakpoint-sm-tablet) overflow-hidden laptop:mx-0 laptop:flex laptop:max-w-full laptop:gap-8">
        <SignupPrompt vectorImgSrc={vectorImgSrc} />
        <Box className="mx-auto w-full px-8 laptop:pt-24">
          <form className="mx-auto flex flex-col gap-6 laptop:max-w-(--breakpoint-sm-tablet)">
            <FormControl>
              <Box>
                <FormLabel component="p">
                  Are you a Washington State resident?{" "}
                  <Box component="span" sx={{ color: "text.disabled" }}>
                    (required)
                  </Box>
                </FormLabel>
              </Box>
              <RadioGroup name="resident">
                <FormControlLabel
                  value="yes"
                  control={<Radio />}
                  label="Yes"
                  onClick={() => setResident(true)}
                />
                <FormControlLabel
                  value="no"
                  control={<Radio />}
                  label="No"
                  onClick={() => setResident(false)}
                />
              </RadioGroup>
            </FormControl>
            <FormControl disabled={!resident}>
              <FormLabel component="legend">Notifications</FormLabel>

              <FormControlLabel
                control={
                  <Checkbox
                    checked={checkboxState.jobNotifications}
                    onChange={handleCheckboxChange}
                    name="jobNotifications"
                  />
                }
                label="Receive new job posting notifications"
              />

              <FormControlLabel
                control={
                  <Checkbox
                    checked={checkboxState.opportunities}
                    onChange={handleCheckboxChange}
                    name="opportunities"
                  />
                }
                label="Hear more about career opportunities"
              />

              <FormControlLabel
                control={
                  <Checkbox
                    checked={checkboxState.termsAgree}
                    onChange={handleCheckboxChange}
                    name="termsAgree"
                  />
                }
                label={
                  <>
                    By signing up you agree to our{" "}
                    <Link target="_blank" href="/policies/terms-of-service">
                      terms of use
                    </Link>
                    .
                  </>
                }
              />
            </FormControl>
            <PillButton
              type="submit"
              onClick={async (e: FormEvent) => {
                e.preventDefault();
                console.log(JSON.stringify(checkboxState));
                const response = await fetch("/api/jobseekers/create", {
                  method: "POST",
                  headers: {
                    "Content-Type": "application/json",
                  },
                  body: JSON.stringify(checkboxState),
                });
                if (response.ok) {
                  const data = await response.json();
                  let rolesArray = session?.user.roles || [];
                  rolesArray = rolesArray.filter(
                    (role: Role) => role !== Role.GUEST,
                  );
                  // Add the new role if it's not already in the roles array
                  if (!rolesArray.includes(Role.JOBSEEKER)) {
                    rolesArray.push(Role.JOBSEEKER);
                  }
                  await updateSessionProperties({
                    jobseekerId: data.result.jobseeker_id,
                    roles: rolesArray,
                  });
                  router.push("/edit-profile/jobseeker/introduction");
                }
              }}
              sx={{
                marginX: "auto",
                marginY: 4,
              }}
              disabled={!(resident && checkboxState.termsAgree)}
            >
              Create account
            </PillButton>
          </form>
        </Box>
        <Image
          src={vectorImgSrc}
          width={1092}
          height={1040}
          className="hidden h-1/2 pt-16 sm-tablet:block laptop:hidden"
          alt="Art of jobseeker"
        />
      </main>

      <footer className="mt-auto pt-8 sm-tablet:hidden">
        <Footer />
      </footer>
    </>
  );
}
