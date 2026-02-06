"use client";

import React, { useEffect } from "react";
import Confetti from "@/app/ui/components/Confetti";
// REVIEW: testing redux
// import type { RootState } from '@/lib/store';
// import { useSelector, useDispatch } from 'react-redux';
// import { addField, updateField } from '@/lib/features/profileCreation/formSlice';
import PillButton from "@/app/ui/components/PillButton";
import { useRouter } from "next/navigation";
import { useSession } from "next-auth/react";

export default function EmployerCongratsPage() {
  // const { fields } = useSelector((state: RootState) => state.form);
  // const dispatch = useDispatch();

  const { data: session, status } = useSession();
  const router = useRouter();

  useEffect(() => {
    console.log("useEffect: status, session", status, session);
    if (status === "authenticated" && session?.user?.employerId) {
      const fetchData = async () => {
        try {
          const response = await fetch(`/api/employers/validate-profile`, {
            method: "PATCH", // Specify the PATCH method
            headers: {
              "Content-Type": "application/json", // Set the content type
            },
          });
          if (!response.ok) {
            throw new Error("Failed to validate employer profile.");
          }
        } catch (error) {
          console.error("Error fetching employer preferences:", error);
        }
      };
      fetchData();
    }
  }, [status, session]);

  function handleClick() {
    router.push("/services/employers/dashboard");
  }

  return (
    <main className="flex justify-center">
      <aside className="profile-form-aside"></aside>
      <section className="profile-form-section main-content">
        <Confetti />
        <h1>{`Congrats on completing your profile, ${session?.user?.firstName}!`}</h1>

        <p className="subtitle-congrats">
          {"Let's kickstart your candidate search journey!"}
        </p>
        <PillButton onClick={handleClick}>Get Started</PillButton>

        {/* <form onSubmit={ handleSubmit }>

          <fieldset>
            <div>
              <fieldset>
                <legend>What are you looking for?</legend>
                <div className="container">
                  <PillButton
                      className="custom-outline-btn inline-block m-2"
                      // variant="outlined"
                      onClick={ () => { setEmploymentType('Full-time job')} }
                  >
                    Full-time job
                  </PillButton>
                  <PillButton
                      className="custom-outline-btn inline-block m-2"
                      // variant="outlined"
                      onClick={ () => { setEmploymentType('Part-time job')} }
                  >
                    Part-time job
                  </PillButton>
                  <PillButton
                      className="custom-outline-btn inline-block m-2"
                      // variant="outlined"
                      onClick={ () => { setEmploymentType('Internship')} }
                  >
                    Internship
                  </PillButton>
                  <PillButton
                      className="custom-outline-btn inline-block m-2"
                      // variant="outlined"
                      onClick={ () => { setEmploymentType('On-campus job')} }
                  >
                    On-campus job
                  </PillButton>
                  <PillButton
                      className="custom-outline-btn inline-block m-2"
                      // variant="outlined"
                      onClick={ () => { setEmploymentType('Contract')} }
                  >
                    Contract
                  </PillButton>
                </div>
              </fieldset>
              <FormControl component="fieldset">
                <FormLabel id="profile-creation-preferences-require-role" className="mt-7" component="legend" sx={{color:"#000000ff"}}>What is your tech role/targeted pathway?</FormLabel>
                <RadioGroup
                  aria-labelledby="profile-creation-preferences-require-role"
                  defaultValue="female"
                  name="profile-creation-preferences-require-role"
                  value={ pathway }
                  onChange = { (e) => { setPathway(e.target.value) } }
                >
                  <FormControlLabel value="Software Development" control={<Radio />} label="Software Development" />
                  <FormControlLabel value="IT & Cloud Computing" control={<Radio />} label="IT & Cloud Computing" />
                  <FormControlLabel value="Cybersecurity" control={<Radio />} label="Cybersecurity" />
                  <FormControlLabel value="Data Analytics" control={<Radio />} label="Data Analytics" />
                </RadioGroup>
              </FormControl>
            </div>
          </fieldset>

          <div className="profile-form-progress-btn-group">
            <PillButton className="custom-outline-btn">Previous</PillButton>
            <PillButton type="submit">Save and continue</PillButton>
          </div>

        </form> */}
      </section>
    </main>
  );
}
