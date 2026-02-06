import nodemailer from "nodemailer";
import type SMTPTransport from "nodemailer/lib/smtp-transport";

import { type Mailer, type MailerPayload } from "@/lib/smtp/mailer";
import { nodeMailerOptions } from "@/lib/smtp/mailer/node-mailer/node-mailer-options";

export class NodeMailer implements Mailer {
  public sendEmail(
    payload: MailerPayload,
  ): Promise<SMTPTransport.SentMessageInfo> {
    return nodemailer.createTransport(nodeMailerOptions.transport).sendMail({
      from: nodeMailerOptions.from,
      to: payload.recipient,
      subject: payload.subject,
      html: payload.html,
      text: payload.text,
    });
  }
}
