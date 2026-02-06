import styles from "./marketing.module.css";

export default function Challenge() {
  return (
    <>
      {/* Top row: H2 left, emphasized sentence right */}
      <div className={styles.challengeTop}>
        <h2 className={styles.challengeHeading}>
          The Challenge
          <br />
          We're Solving
        </h2>

        <p className={styles.challengeDek}>
          Washington's tech economy is among the strongest in the nation — yet
          the{" "}
          <span className={styles.challengeDekEmph}>
            AI skills gap is widening.
          </span>
        </p>
      </div>

      {/* Bottom row: three points */}
      <div className={styles.challengeGrid}>
        <p className={styles.challengePoint}>
          74% of employers report difficulty hiring AI-literate developers.
        </p>
        <p className={styles.challengePoint}>
          Entry-level software roles are shifting toward AI-assisted
          productivity.
        </p>
        <p className={styles.challengePoint}>
          Most training programs haven't yet caught up to the new reality of
          AI-augmented engineering.
        </p>
      </div>
    </>
  );
}
