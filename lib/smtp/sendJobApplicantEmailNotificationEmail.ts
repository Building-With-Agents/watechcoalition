"use server";
import { render } from "@react-email/render";
import { sendEmail } from "@/lib/smtp/mailer/send-email";
import { getAllCareerNavigators } from "@/app/lib/admin/careerPrep";
import {
  ApplicantJobStatusUpdateEmailNotification,
  CareerPrepJobStatusNotificationData,
} from "@/emails/ApplicantJobStatusUpdateEmailNotification";

export async function sendJobApplicantEmailNotificationEmail(
  data: CareerPrepJobStatusNotificationData,
) {
  const careerNavs = await getAllCareerNavigators();
  if (!careerNavs) return;
  careerNavs.forEach((cn) => {
    sendSingleJobApplicantEmailNotificationEmail({
      recipient: cn.email,
      ...data,
    });
  });
}

async function sendSingleJobApplicantEmailNotificationEmail(
  data: CareerPrepJobStatusNotificationData & { recipient: string },
) {
  const component = ApplicantJobStatusUpdateEmailNotification(data);
  const html = await render(component);
  const text = await render(component, { plainText: true });
  await sendEmail({
    recipient: data.recipient,
    subject: `New Case Available`,
    html,
    text,
  });
}
