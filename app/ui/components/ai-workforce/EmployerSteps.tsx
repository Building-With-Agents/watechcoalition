import styles from "./marketing.module.css";

export default function EmployerSteps() {
  return (
    <div className={styles.stepsBoard}>
      <div className={styles.stepCol}>
        <div className={styles.stepKicker}>Step 1</div>
        <div className={styles.stepTitle}>Signaling</div>
        <p className={styles.stepBody}>
          Employers signal evolving AI skill needs.
        </p>
      </div>

      <div className={styles.stepCol}>
        <div className={styles.stepKicker}>Step 2</div>
        <div className={styles.stepTitle}>Analysis</div>
        <p className={styles.stepBody}>
          WTWC analyzes and shares insights across education and workforce
          partners.
        </p>
      </div>

      <div className={styles.stepCol}>
        <div className={styles.stepKicker}>Step 3</div>
        <div className={styles.stepTitle}>Upskill</div>
        <p className={styles.stepBody}>
          Educators update curricula, and job seekers upskill accordingly.
        </p>
      </div>

      <div className={styles.stepCol}>
        <div className={styles.stepKicker}>Step 4</div>
        <div className={styles.stepTitle}>Access</div>
        <p className={styles.stepBody}>
          Employers gain access to pre-qualified, AI-ready developers.
        </p>
      </div>
    </div>
  );
}
