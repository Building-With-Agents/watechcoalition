import { type Mailer } from "@/lib/smtp/mailer";

export async function resolveMailer(): Promise<Mailer> {
  let mailer = process.env.EMAIL_MAILER as string;

  if (mailer) {
    mailer = mailer.toLowerCase();

    if (mailer === "nodemailer") {
      const importedModule = await import("@/lib/smtp/mailer/node-mailer");
      return new importedModule.NodeMailer();
    }

    if (mailer === "resend") {
      const importedModule = await import("@/lib/smtp/mailer/resend");
      return new importedModule.ResendMailer();
    }
  }

  // Default to node mailer
  const importedModule = await import("@/lib/smtp/mailer/node-mailer");
  return new importedModule.NodeMailer();
}
