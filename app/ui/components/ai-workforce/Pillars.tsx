import styles from "./marketing.module.css";

export default function Pillars() {
  return (
    <>
      <section className={styles.sectionHeadingWrap}>
        <h2 className={styles.sectionHeading}>What We've Built</h2>
      </section>

      <div className={styles.pillarsGrid}>
        <div className={styles.pillar}>
          <div className={styles.pillarTitle}>AI Foundations:</div>
          <div className={styles.pillarBody}>
            Reasoning with LLMs, prompt engineering, applied machine learning.
          </div>
        </div>

        <div className={styles.pillar}>
          <div className={styles.pillarTitle}>Full-Stack Development</div>
          <div className={styles.pillarBody}>
            Front-end, back-end, DevOps, APIs, cloud.
          </div>
        </div>

        <div className={styles.pillar}>
          <div className={styles.pillarTitle}>AI Integration</div>
          <div className={styles.pillarBody}>
            Agentic workflows, tool orchestration, embeddings, RAG systems.
          </div>
        </div>

        <div className={styles.pillar}>
          <div className={styles.pillarTitle}>
            Responsible AI & Collaboration
          </div>
          <div className={styles.pillarBody}>
            Ethics, teamwork, versioning, model evaluation.
          </div>
        </div>
      </div>
    </>
  );
}
