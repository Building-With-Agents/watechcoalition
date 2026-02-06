import { render } from "@react-email/render";

import {
  InvitationEmail,
  type InvitationEmailData,
} from "@/emails/invitation-email";
import { sendEmail } from "@/lib/smtp/mailer/send-email";

export async function sendInvitationEmail(
  data: InvitationEmailData,
): Promise<void> {
  const component = InvitationEmail(data);
  const html = await render(component);
  const text = await render(component, { plainText: true });

  await sendEmail({
    recipient: data.recipient,
    subject: "Organization invitation",
    html,
    text,
  });
}
