import { type MailerPayload } from "@/lib/smtp/mailer";
import { resolveMailer } from "@/lib/smtp/mailer/resolve-mailer";

export async function sendEmail(payload: MailerPayload): Promise<unknown> {
  const mailer = await resolveMailer();
  return mailer.sendEmail(payload);
}
