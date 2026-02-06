import { render } from "@react-email/render";

import { sendEmail } from "@/lib/smtp/mailer/send-email";
import {
  EmployerNeedsVerificationData,
  EmployerNeedsVerificationEmail,
} from "@/emails/employer-needs-verification-email";

export async function sendEmployerOrCompanyNeedsApprovalEmailToGary(
  data: EmployerNeedsVerificationData,
): Promise<void> {
  const component = EmployerNeedsVerificationEmail(data);
  const html = await render(component);
  const text = await render(component, { plainText: true });

  await sendEmail({
    recipient: data.recipient,
    subject: "Approval Needed On Talent Portal",
    html,
    text,
  });
}
