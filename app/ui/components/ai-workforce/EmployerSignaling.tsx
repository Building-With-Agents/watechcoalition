// components/wtwc/EmployerSignaling.tsx
import styles from "./marketing.module.css";

export default function EmployerSignaling() {
  return (
    <div className={styles.essGrid}>
      <h2 className={styles.essHeading}>
        How The Employer
        <br />
        Signaling System
        <br />
        Works
      </h2>

      <p className={styles.essDek}>
        It's a <span className={styles.essEmph}>feedback loop</span> designed to
        keep WA's tech workforce agile, inclusive, and future-proof.
      </p>
    </div>
  );
}
