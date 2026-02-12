import { type Mailer } from "@/lib/smtp/mailer";

export async function resolveMailer(): Promise<Mailer> {
  const importedModule = await import("@/lib/smtp/mailer/resend");
  return new importedModule.ResendMailer();
}
