// components/wtwc/BeFirstToKnow.tsx
"use client";

import { useState } from "react";
import styles from "./marketing.module.css";

export default function BeFirstToKnow() {
  const [formData, setFormData] = useState({
    firstName: "",
    lastName: "",
    email: "",
    phone: "",
  });
  const [successfullySubmitted, setSuccessfullySubmitted] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    // Flat payload matching SharePoint column names
    const payload = {
      Title: "AI Workforce Contact",
      FirstName: formData.firstName.trim(),
      LastName: formData.lastName.trim(),
      Email: formData.email.trim(),
      PhoneNumber: formData.phone.trim(),
      SubmissionDate: new Date().toISOString(),
    };
    console.log("Form submission payload:", JSON.stringify(payload, null, 2));
    try {
      const res = await fetch("/api/ai-workforce/contacts/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) throw new Error("Submission failed");

      setSuccessfullySubmitted(true);
      setFormData({ firstName: "", lastName: "", email: "", phone: "" });
    } catch (error) {
      setErrorMessage("Submission failed. Please try again.");
    }
  };

  if (successfullySubmitted) {
    return (
      <div className={styles.btfkContainer}>
        <div
          style={{
            gridColumn: "1 / -1",
            textAlign: "center",
            padding: "60px 20px",
          }}
        >
          <h2 className={styles.btfkFormTitle}>Thank You!</h2>
          <p className={styles.btfkDescription} style={{ marginTop: "20px" }}>
            We've received your information and will be in touch soon.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.btfkContainer}>
      {/* Left column: Main title */}
      <div className={styles.btfkLeftColumn}>
        <h3 className={styles.btfkMainTitle}>
          Test out the Developer Skill Map and Employer Signaling System.
        </h3>
      </div>

      {/* Middle column: Description text */}
      <div className={styles.btfkMiddleColumn}>
        <p className={styles.btfkDescription}>
          Help shape the standards, pilot the data, and prepare your
          organization — or your career — for what's next.
        </p>
      </div>

      {/* Right column: Form title and form */}
      <div className={styles.btfkRightColumn}>
        <h2 className={styles.btfkFormTitle}>Be The First To Know</h2>

        <form className={styles.btfkForm} onSubmit={handleSubmit}>
          <div className={styles.btfkFormGrid}>
            <label className={styles.btfkField}>
              <span className={styles.btfkLabel}>First Name</span>
              <input
                className={styles.btfkInput}
                placeholder="Jane"
                value={formData.firstName}
                onChange={(e) =>
                  setFormData({ ...formData, firstName: e.target.value })
                }
                required
              />
            </label>

            <label className={styles.btfkField}>
              <span className={styles.btfkLabel}>Last Name</span>
              <input
                className={styles.btfkInput}
                placeholder="Smith"
                value={formData.lastName}
                onChange={(e) =>
                  setFormData({ ...formData, lastName: e.target.value })
                }
                required
              />
            </label>

            <label className={styles.btfkField}>
              <span className={styles.btfkLabel}>Email</span>
              <input
                className={styles.btfkInput}
                placeholder="jane12345@gmail.com"
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                required
              />
            </label>

            <label className={styles.btfkField}>
              <span className={styles.btfkLabel}>Phone Number</span>
              <input
                className={styles.btfkInput}
                placeholder="(206) 555-0100"
                type="tel"
                pattern="^(?:\+(?=(?:\D*\d){6,15}$)\d{1,3}(?:[ .-]?(?:\(\d{1,4}\)|\d{1,4})){2,5}|\(?\d{3}\)?[ .-]?\d{3}[ .-]?\d{4}|\d{10})$"
                title="Enter a valid phone number, e.g.: 3603229617, (206) 555-0100, 206-555-0100, 206.555.0100, 555.555.5555, +1 206-555-0100, +1 (206) 555-0100, +44 20 7946 0958"
                value={formData.phone}
                onChange={(e) =>
                  setFormData({ ...formData, phone: e.target.value })
                }
              />
            </label>
          </div>

          {errorMessage && (
            <div
              style={{ color: "#dc2626", fontSize: "14px", marginTop: "8px" }}
            >
              {errorMessage}
            </div>
          )}

          <button className={styles.btfkButton} type="submit">
            Preview The Framework
          </button>
        </form>
      </div>
    </div>
  );
}
