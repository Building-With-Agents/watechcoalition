/**
 * Enum representing the different states of a job application process.
 *
 * **Process Flow:**
 * 1. **Applied**:
 *    - Set by the jobseeker when submitting an application.
 *    - Notifies the case manager that the application requires screening.
 *
 * 2  **Contacted**
 *    - Set by Career Navigator
 *    - Records that the jobseeker has been contacted.
 *
 * 3. **Screening Scheduled**
 *    - Set by the Career Navigator
 *    - Indicates that a screening meeting has been scheduled.
 *
 * 4. **I Withdrew**:
 *    - Set by the jobseeker if they decide to withdraw their application.
 *    - This option is only available while the application is in the `Applied` state.
 *
 * 5. **Screened**:
 *    - Set by the case manager after completing the screening process.
 *    - Indicates that the jobseeker has been evaluated and is ready for further consideration.
 *
 * 6. **Recommended**:
 *    - Set by the Career Navigator
 *    - Indicates they have done screening and should be passed along to the employer.
 *
 * 7. **Interviewing**, **Negotiating**, **Accepted**, **Not Selected**, **No Response**:
 *    - Can be set by either the employer (when reviewing screened candidates via their dashboard)
 *      or a career navigator (through the Career Prep dashboard).
 *    - Reflects the progression of the application through the selection process.
 *
 * **Important Notes:**
 * - Once the application progresses beyond the `Applied` state, the jobseeker can no longer withdraw
 *   their application. This ensures accurate tracking of how far each candidate has advanced for reporting purposes.
 * - All status changes are critical for monitoring application progress and maintaining proper records
 *   for both administrative and reporting needs.
 */
export enum JobStatus {
  Applied = "Applied",
  Contacted = "Contacted",
  ScreeningScheduled = "Screening Scheduled",
  Screened = "Screened",
  Recommended = "Recommended",
  Interviewing = "Interviewing",
  Negotiating = "Negotiating",
  Accepted = "Accepted",
  IWithdrew = "I Withdrew",
  NotSelected = "Not Selected",
  NoResponse = "No Response",
}
