import { render } from "@react-email/render";

import { WelcomeEmail, type WelcomeEmailData } from "@/emails/welcome-email";
import { sendEmail } from "@/lib/smtp/mailer/send-email";

export async function sendWelcomeEmail(data: WelcomeEmailData): Promise<void> {
  const component = WelcomeEmail(data);
  const html = await render(component);
  const text = await render(component, { plainText: true });

  await sendEmail({
    recipient: data.recipient,
    subject: `Welcome to Wa Tech`,
    html,
    text,
  });
}
