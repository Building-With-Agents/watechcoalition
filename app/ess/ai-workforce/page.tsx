import Hero from "@/app/ui/components/ai-workforce/Hero";
import Pillars from "@/app/ui/components/ai-workforce/Pillars";
import Banner from "@/app/ui/components/ai-workforce/Banner";
import EmployerSignaling from "@/app/ui/components/ai-workforce/EmployerSignaling";
import EmployerSteps from "@/app/ui/components/ai-workforce/EmployerSteps";
import WhyCare from "@/app/ui/components/ai-workforce/WhyCare";
import Challenge from "@/app/ui/components/ai-workforce/Challenge";
import EmployerChangeBanner from "@/app/ui/components/ai-workforce/EmployerChangeBanner";
import BeFirstToKnow from "@/app/ui/components/ai-workforce/BeFirstToKnow";
import styles from "@/app/ui/components/ai-workforce/marketing.module.css";

export default function WtwcPage() {
  return (
    <>
      <main className={styles.aiWorkforcePage}>
        <Hero />
        <Pillars />
        <Banner />
        <EmployerSignaling />
        <EmployerSteps />
        <WhyCare />
        <Challenge />
        <EmployerChangeBanner />
        <BeFirstToKnow />
      </main>
    </>
  );
}
