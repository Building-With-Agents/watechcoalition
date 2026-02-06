import { render } from "@react-email/render";

import {
  VerifyEmailAddressEmail,
  type VerifyEmailAddressEmailData,
} from "@/emails/verify-email-address-email";
import { sendEmail } from "@/lib/smtp/mailer/send-email";

export async function sendVerifyEmailAddressEmail(
  data: VerifyEmailAddressEmailData,
): Promise<void> {
  const component = VerifyEmailAddressEmail(data);
  const html = await render(component);
  const text = await render(component, { plainText: true });

  await sendEmail({
    recipient: data.recipient,
    subject: "Verify email address",
    html,
    text,
  });
}
