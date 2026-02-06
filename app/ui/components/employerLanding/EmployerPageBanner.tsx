import Image from "next/image";
import PillButton from "../PillButton";

export default async function EmployerPageBanner() {
  return (
    <div
      className={
        "laptop:h-[825px] phone:h-[1300px] grid items-center gap-[64px] laptop:grid-cols-2 bg-linear-to-b from-[#014260] to-[#39b2c2] px-[16px] py-[128px] sm-tablet:px-[50px] laptop:px-[100px] text-white"
      }
    >
      <Image
        src={"/images/employers/Profile-Card.png"}
        className="justify-self-center max-w-8/10"
        alt={""}
        width={611}
        height={632}
      />
      <div className="laptop:order-first space-y-7">
        <div
          className="self-stretch capitalize leading-tight"
          style={{ fontSize: "clamp(2rem, 10vw, 5rem)" }}
        >
          Your Hiring Concierge for WA Tech Talent
        </div>
        <div className="self-stretch text-[22px] leading-relaxed">
          Stop sifting through résumés. Access a pre‑vetted pipeline of 1000+
          skilled tech job seekers from 15+ colleges and training partners
          statewide.
        </div>
        <div className="gap-4 flex flex-row items-start justify-start">
          <PillButton
            variant="outlined"
            size="large"
            href={"/about-us"}
            sx={{ color: "neutral.black", backgroundColor: "primary.light" }}
          >
            Learn More
          </PillButton>
          <PillButton
            variant="outlined"
            color="inherit"
            size="large"
            href={"mailto:susanne.mata@computingforall.org"}
          >
            Get In Touch
          </PillButton>
        </div>
      </div>
    </div>
  );
}
