import { detectTransport } from "@/lib/smtp/mailer/node-mailer/detect-transport";
import type { NodeMailerTransport } from "@/lib/smtp/mailer/node-mailer/node-mailer-transport";

type NodeMailerOptions = {
  transport: NodeMailerTransport;
  from: string;
};

export const nodeMailerOptions: NodeMailerOptions = {
  transport: detectTransport(),
  from: process.env.EMAIL_SENDER as string,
};
