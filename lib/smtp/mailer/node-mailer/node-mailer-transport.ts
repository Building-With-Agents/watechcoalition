import type SendmailTransport from "nodemailer/lib/sendmail-transport";
import type SMTPConnection from "nodemailer/lib/smtp-connection";

export type NodeMailerTransport =
  | SendmailTransport.Options
  | SMTPConnection.Options
  | string;
