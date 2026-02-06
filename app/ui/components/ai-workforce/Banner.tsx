import Image from "next/image";
import styles from "./marketing.module.css";
import bg from "@/public/images/ai-workforce/abstract.jpg";

export default function Banner() {
  return (
    <div className={styles.banner}>
      {/* Background image (decorative) */}
      <Image
        src={bg}
        alt=""
        role="presentation"
        fill
        className={styles.bannerImg}
        sizes="(max-width: 1200px) 100vw, 1080px"
        priority={false}
      />
      <div className={styles.bannerOverlay} />
      <p className={styles.bannerText}>
        CFA and WTWC Full-Stack Developer Skill Map — a shared framework that
        defines what AI-ready development looks like.
      </p>
    </div>
  );
}
