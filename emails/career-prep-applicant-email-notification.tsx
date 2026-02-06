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

export type CareerPrepNotificationData = {
  recipient: string;
  navigatorName: string;
  applicantName: string;
};

export const CareerNewPrepApplicantEmailNotification = ({
  navigatorName,
}: CareerPrepNotificationData) => (
  <Html>
    <Head />
    <Preview>New Career Prep Case Available!</Preview>
    <Tailwind>
      <Body className="m-auto bg-white px-2 font-sans">
        <Container className="mx-auto my-[40px] max-w-[465px] rounded border border-solid border-[#eaeaea] p-[20px]">
          <Heading className="mx-0 my-[30px] p-0 text-center text-[24px] font-normal text-black">
            New Career Prep Case(s) Available!
          </Heading>
          <Text className="text-[14px] leading-[24px] text-black">
            Hello {navigatorName},
          </Text>
          <Text className="text-[14px] leading-[24px] text-black">
            There has been a new application to the career prep platform that
            needs your attention.
          </Text>
          <Section className="my-[32px] text-center">
            <Button
              className="rounded bg-neutral-black px-5 py-3 text-center text-[12px] font-semibold text-white no-underline"
              href={`https://www.watechcoalition.org/career-prep/new-cases`}
            >
              Claim or View New Cases Here
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
