import { Resend, type CreateEmailResponse } from "resend";

import { type Mailer, type MailerPayload } from "@/lib/smtp/mailer";
import { resendOptions } from "@/lib/smtp/mailer/resend/resend-options";

const resend = new Resend(process.env.EMAIL_RESEND_API_KEY);

export class ResendMailer implements Mailer {
  public async sendEmail(payload: MailerPayload): Promise<CreateEmailResponse> {
    const response = await resend.emails.send({
      from: resendOptions.from,
      to: payload.recipient,
      subject: payload.subject,
      html: payload.html,
      text: payload.text,
    });
    if (response.error) {
      throw Error(response.error.message ?? "Could not send mail.");
    }

    return response;
  }
}
