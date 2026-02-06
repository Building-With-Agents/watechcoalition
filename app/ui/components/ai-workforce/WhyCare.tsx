import styles from "./marketing.module.css";

export default function WhyCare() {
  return (
    <>
      <h2 className={styles.sectionHeadingCenter}>Why Should You Care</h2>

      <div className={styles.whyCareGrid}>
        <div className={styles.whyCard}>
          <div className={styles.whyTitle}>For developers:</div>
          <p className={styles.whyBody}>
            → A clear roadmap to upskill and evolve from traditional to
            AI-enabled roles.
          </p>
        </div>

        <div className={styles.whyCard}>
          <div className={styles.whyTitle}>For employers:</div>
          <p className={styles.whyBody}>
            → A shared framework to assess AI-readiness, design reskilling
            programs, and hire confidently.
          </p>
        </div>

        <div className={styles.whyCard}>
          <div className={styles.whyTitle}>
            For educators & training partners:
          </div>
          <p className={styles.whyBody}>
            → A blueprint to create applied AI curricula aligned with real-world
            roles and employer demand.
          </p>
        </div>
      </div>
    </>
  );
}
