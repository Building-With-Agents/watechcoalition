export type MailerPayload = {
  recipient: string;
  subject: string;
  text: string;
  html: string;
};

export interface Mailer {
  sendEmail(payload: MailerPayload): Promise<unknown>;
}
