import styles from "./marketing.module.css";
import { ReactNode } from "react";

export default function SectionHeading({ children }: { children: ReactNode }) {
  return (
    <section className={styles.sectionHeadingWrap}>
      <h2 className={styles.sectionHeading}>{children}</h2>
    </section>
  );
}
