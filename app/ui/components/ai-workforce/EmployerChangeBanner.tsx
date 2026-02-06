import Image from "next/image";
import styles from "./marketing.module.css";
import bg from "@/public/images/ai-workforce/keyboard-blur.jpg"; // replace with your asset

export default function EmployerChangeBanner() {
  return (
    <div className={styles.containerWide}>
      <div className={styles.changeBanner}>
        <Image
          src={bg}
          alt=""
          role="presentation"
          fill
          priority={false}
          className={styles.changeBannerImg}
          sizes="(max-width: 1368px) 100vw, 1368px"
        />
        <div className={styles.changeBannerScrim} />
        <p className={styles.changeBannerText}>
          Our Employer Signaling System changes that — aligning skill data,
          training pathways, and hiring pipelines across the state.
        </p>
      </div>
    </div>
  );
}
