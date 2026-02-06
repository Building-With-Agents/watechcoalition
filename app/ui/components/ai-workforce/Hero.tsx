"use client";

import Image from "next/image";
import styles from "./marketing.module.css";
import heroImg from "@/public/images/ai-workforce/hero-keyboard.jpg"; // drop in your exported 1280×853 asset

export default function Hero() {
  return (
    <section className={styles.heroWrap}>
      <div className={styles.heroInner}>
        <h1 className={styles.heroTitle}>
          The future of software development starts here.
          <br />
          At WTWC, we are building WA AI-ready workforce — together.
        </h1>

        <div className={styles.heroGrid}>
          <div className={styles.heroImageFrame}>
            {/* Using next/image for perf; explicit width/height preserves aspect ratio */}
            <Image
              src={heroImg}
              alt="Hands on laptop keyboard"
              className={styles.heroImage}
              priority
              width={645}
              height={427}
              sizes="(max-width: 1024px) 100vw, 645px"
            />
          </div>

          <p className={styles.heroDeck}>
            AI is redefining the software developer’s role — from writing code
            to reasoning with systems that can code for themselves. Across
            Washington, employers, educators, and developers are joining forces
            to ensure our workforce stays ahead of the curve.
          </p>
        </div>
      </div>
    </section>
  );
}
