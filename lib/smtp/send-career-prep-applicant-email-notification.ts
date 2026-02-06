import {
  CareerNewPrepApplicantEmailNotification,
  CareerPrepNotificationData,
} from "@/emails/career-prep-applicant-email-notification";
import { render } from "@react-email/render";
import { sendEmail } from "@/lib/smtp/mailer/send-email";
import { getAllCareerNavigators } from "@/app/lib/admin/careerPrep";

export async function sendCareerPrepApplicantEmailNotificationEmail(
  applicantName: string,
) {
  const careerNavs = await getAllCareerNavigators();
  if (!careerNavs) return;
  careerNavs.forEach((cn) => {
    sendSingleCareerPrepApplicantEmailNotificationEmail({
      recipient: cn.email,
      applicantName: applicantName,
      navigatorName: `${cn.first_name} ${cn.last_name}`,
    });
  });
}

async function sendSingleCareerPrepApplicantEmailNotificationEmail(
  data: CareerPrepNotificationData,
) {
  const component = CareerNewPrepApplicantEmailNotification(data);
  const html = await render(component);
  const text = await render(component, { plainText: true });
  await sendEmail({
    recipient: data.recipient,
    subject: `New Case Available`,
    html,
    text,
  });
}
