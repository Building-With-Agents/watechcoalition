import {
  Body,
  Button,
  Container,
  Head,
  Heading,
  Hr,
  Html,
  Preview,
  Section,
  Text,
} from "@react-email/components";
import { Tailwind } from "@react-email/tailwind";

//import { AppInfo } from '@/constants/app-info';
//import { Routes } from '@/constants/routes';
//import { getBaseUrl } from '@/lib/urls/get-base-url';

export type CareerPrepJobStatusNotificationData = {
  navigatorName: string;
  applicantName: string;
  jobId: string;
  jobTitle: string;
  Company: string;
};

export const ApplicantJobStatusUpdateEmailNotification = (
  data: CareerPrepJobStatusNotificationData,
) => (
  <Html>
    <Head />
    <Preview>{`New Applicant for ${data.jobTitle} @ ${data.Company}`}</Preview>
    <Tailwind>
      <Body className="m-auto bg-white px-2 font-sans">
        <Container className="mx-auto my-[40px] max-w-[465px] rounded border border-solid border-[#eaeaea] p-[20px]">
          <Heading className="mx-0 my-[30px] p-0 text-center text-[24px] font-normal text-black">
            {`New Applicant for ${data.jobTitle} @ ${data.Company}`}
          </Heading>
          <Text className="text-[14px] leading-[24px] text-black">
            Hello {data.navigatorName},
          </Text>
          <Text className="text-[14px] leading-[24px] text-black">
            {`${data.applicantName} has applied to ${data.jobTitle} @ ${data.Company}`}
          </Text>
          <Section className="my-[32px] text-center">
            <Button
              className="rounded bg-neutral-black px-5 py-3 text-center text-[12px] font-semibold text-white no-underline"
              href={`https://www.watechcoalition.org/career-prep/placement-tracking`}
            >
              View Updates Here
            </Button>
          </Section>
          <Text className="text-[14px] leading-[24px] text-black">
            If you have any questions or need assistance, please don't hesitate
            to reach out to our support team.
          </Text>
          <Hr className="mx-0 my-[26px] w-full border border-solid border-[#eaeaea]" />
          <Text className="text-[12px] leading-[24px] text-[#666666]">
            You receive this email because you are registered as a Career
            Navigator on https://www.watechcoalition.org/.
          </Text>
        </Container>
      </Body>
    </Tailwind>
  </Html>
);
