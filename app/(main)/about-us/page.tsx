import Image from "next/image";
import Link from "next/link";
import RoundedButton from "@/app/ui/components/RoundedButton";
import { List, ListItem } from "@mui/material";

export const metadata = {
  title: "About Us",
  description:
    "A Community Developing a Diverse, highly skilled Technology Workforce in Washington State",
};

// Force server-side rendering, to get latest training provider logos
export const dynamic = "force-dynamic";

export default function page() {
  return (
    <main>
      <header
        className="box-border bg-blue-100 px-[1em] py-[128.55px]"
        id="about-us-header"
      >
        <h1 className="mx-auto max-w-[1535px] text-center font-['Roboto'] text-[22px] font-semibold uppercase text-gray-800">
          About Us
        </h1>
        <p className="text-fluid-lg leading-fluid-lg mx-auto max-w-[1535px] text-center font-['Roboto'] font-normal capitalize text-blue-text2">
          A Community Developing a Diverse, highly skilled Technology Workforce
          in Washington State
        </p>
      </header>
      <section
        className="box-border bg-white px-[1em] py-[60px] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-text"
        id="about-us-intro"
      >
        <div className="mx-auto max-w-[1235px] space-y-[50px]">
          <Image
            src="/images/TWC_75x50_2024.svg"
            width={201}
            height={128}
            alt="Tech Workforce Coalition's Logo"
            className="mx-auto max-w-[201px]"
          />
          <div className="space-y-[30.80px]">
            <p>
              The{" "}
              <b className="font-semibold text-blue-text2">
                Tech Workforce Coalition
              </b>{" "}
              bridges Washington’s gaps in critical IT/Cybersecurity jobs.​
              Aligning job candidate competencies with advances in technology.
              Guided by AWS, Microsoft, Accenture, ​ and WTIA, the Coalition
              creates a platform for the state’s postsecondary education and
              training institutions ​ to address industry priorities.​ Providing
              your organization access to unique sources of quality talent. Our
              Talent Finder Portal taps into​ talent pools that are not easily
              accessible in traditional job boards. You’ll have direct access to
              quality ​ candidates from:​
            </p>
            <List>
              <ListItem>• Colleges with AWS curriculum​</ListItem>
              <ListItem>
                • Colleges with curriculum funded by the National Science
                Foundation​
              </ListItem>
              <ListItem>• Colleges with AI curriculum​</ListItem>
              <ListItem>
                • Training partners delivering candidates with industry-valued
                credentials​
              </ListItem>
            </List>
          </div>
          <header className="text-center">
            <h2 className="font-semibold uppercase leading-snug">Our Goal</h2>
            <p className="text-[44px] capitalize leading-[61.60px] text-gray-800">
              <b className="text-fluid-xl leading-fluid-xl block font-normal text-blue-text2">
                1,000 job candidates
              </b>{" "}
              in tech roles by 2026
            </p>
          </header>
        </div>
      </section>
      <section
        className="box-border space-y-[68px] bg-gray-background3 px-[1em] pb-[34px] pt-[54px] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800"
        id="about-us-strategy"
      >
        <div className="mx-auto block max-w-[1235px] items-center laptop:flex laptop:gap-x-[50px]">
          <div className="space-y-[20px]">
            <header>
              <h2 className="font-semibold uppercase leading-snug">
                Coalition{" "}
                <b className="text-fluid-lg leading-fluid-lg-snug block pt-[20px] font-normal capitalize text-blue-textdark2">
                  Strategy
                </b>
              </h2>
            </header>
            <p>
              Our mission is to connect underrepresented candidates with
              in-demand tech jobs. We offer targeted training programs in IT and
              cybersecurity, along with personalized career coaching and
              networking opportunities. By bridging the gap between talent and
              opportunity, we are working to build a more diverse and innovative
              tech industry.
            </p>
            <div className="pt-[40px]">
              <RoundedButton
                content="Join the Coalition"
                link="/join"
                invertColor
                snug
                newColors
                bold={false}
                className="capitalize"
              />
            </div>
          </div>
          <figure>
            <Image
              src="/images/about-us/strategy-funnel.svg"
              width={644}
              height={516}
              alt="Depiction of the strategy funnel where Computing For All is placed in-between the Tech Workforce Coalition and the following three entities: Employers, Edu/Training Agents, CBO's"
              className="mx-auto w-full max-w-[644px] laptop:w-[644px]"
            />
            <figcaption className="mt-[20px] text-center font-semibold uppercase text-blue-textdark2">
              IT &amp; Cybersecurity Sector
            </figcaption>
          </figure>
        </div>
        <section className="mx-auto max-w-[1235px] text-center font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800">
          <h3 className="mb-[48px] text-[44px] capitalize leading-[52.80px] text-blue-textdark2">
            Member Roles
          </h3>
          <div className="block laptop:flex laptop:gap-x-[44px]">
            <div className="w-full flex-1 space-y-[10px] laptop:w-auto">
              <h4 className="text-[44px] capitalize leading-[52.80px] text-blue-text2">
                Employers
              </h4>
              <p>
                Businesses of all types and sizes have technology needs. Hire
                vetted, qualified candidates in our Talent Finder Portal.
              </p>
            </div>
            <div className="w-full flex-1 space-y-[10px] laptop:w-auto">
              <h4 className="text-[44px] capitalize leading-[52.80px] text-blue-text2">
                Employer Advisor
              </h4>
              <p>
                Share your recruiting needs with educators and guide technology
                training curricula updates.
              </p>
            </div>
            <div className="w-full flex-1 space-y-[10px] laptop:w-auto">
              <h4 className="text-[44px] capitalize leading-[52.80px] text-blue-text2">
                Educator
              </h4>
              <p>
                Advance curriculum to keep pace with employer needs and connect
                your students directly with employers.
              </p>
            </div>
            <div className="w-full flex-1 space-y-[10px] laptop:w-auto">
              <h4 className="text-[44px] capitalize leading-[52.80px] text-blue-text2">
                Community Partner
              </h4>
              <p>
                Represent your professional, non-profit, or government
                organization, and broaden access to family wage careers for
                diverse candidates.
              </p>
            </div>
          </div>
        </section>
        <section className="mx-auto max-w-[1235px] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800">
          <h3 className="mb-[48px] text-center text-[44px] capitalize leading-[52.80px] text-blue-textdark2">
            Member Activities &amp; Benefits
          </h3>
          <div className="block text-left laptop:flex laptop:gap-x-[50px]">
            <div className="flex-1 space-y-[10px]">
              <Image
                height="278"
                width="378"
                className="w-full max-w-[378px] rounded-[20px]"
                src="/images/about-us/pexels-fauxels-3184322.jpg"
                alt="Stock photo of a group of people varying in age, race, and gender collaborating around a table, where a woman is standing and talking to an older man"
              />
              <h4 className="pt-[40px] text-[44px] capitalize leading-[52.80px] text-blue-text2">
                Biannual Convening
              </h4>
              <p>
                All members enjoy networking with Industry, Education, and
                Community partners to learn best practices for talent
                acquisition and development in these live, biannual events.
              </p>
            </div>
            <div className="flex-1 space-y-[10px]">
              <Image
                height="278"
                width="378"
                className="w-full max-w-[378px] rounded-[20px]"
                src="/images/about-us/image 17.jpg"
                alt="Stock photo of a group of people varying in age, race, and gender collaborating around a table using their paper and electronic notebooks"
              />
              <h4 className="pt-[40px] text-[44px] capitalize leading-[52.80px] text-blue-text2">
                Committees
              </h4>
              <p>
                Members who wish to take on a leadership role are welcome to
                join one of our committees. Meetings are quarterly and scheduled
                in advance.
              </p>
            </div>
            <div className="flex-1 space-y-[10px]">
              <div className="relative h-[277.33px] w-[377px]">
                <div className="absolute left-[36.86px] top-[188.71px] inline-flex flex-col items-start justify-start gap-[8.94px] rounded-lg bg-white p-[9.29px] shadow-xs">
                  <div className="flex flex-col items-start justify-start gap-[2.98px]">
                    <div className="inline-flex items-center justify-start">
                      <div className="flex h-[7.92px] w-[7.92px] items-center justify-center">
                        <div className="inline-flex h-[7.92px] w-[7.92px] items-center justify-center">
                          <div className="relative flex h-[7.92px] w-[7.92px] flex-col items-start justify-start" />
                        </div>
                      </div>
                      <div className="text-center font-['Roboto'] text-[8.94px] font-medium leading-3 text-black/90">
                        Add Projects
                      </div>
                    </div>
                  </div>
                </div>
                <div className="absolute left-[257.29px] top-[129.41px] inline-flex flex-col items-start justify-start gap-[10.06px] rounded-lg bg-white p-[9.29px] shadow-xs">
                  <div className="flex flex-col items-start justify-start gap-[3.35px]">
                    <div className="inline-flex items-center justify-start">
                      <div className="flex h-[8.91px] w-[8.91px] items-center justify-center">
                        <div className="inline-flex h-[8.91px] w-[8.91px] items-center justify-center">
                          <div className="relative flex h-[8.91px] w-[8.91px] flex-col items-start justify-start" />
                        </div>
                      </div>
                      <div className="text-center font-['Roboto'] text-[10.06px] font-medium leading-[13.42px] text-black/90">
                        Add Certificate
                      </div>
                    </div>
                  </div>
                </div>
                <div className="absolute left-0 top-[68.10px] inline-flex h-[37.32px] flex-col items-center justify-start gap-[13.13px]">
                  <div className="flex h-[37.32px] flex-col items-center justify-start gap-[6.57px] self-stretch">
                    <div className="flex h-[37.32px] flex-col items-center justify-start gap-[4.38px] self-stretch">
                      <div className="self-stretch" />
                    </div>
                  </div>
                </div>
                <div className="absolute left-[46.43px] top-[140.52px] inline-flex items-center justify-start rounded-[54.71px] bg-black/10 px-[4.95px] py-[2.48px]">
                  <div className="inline-flex flex-col items-start justify-start px-[3.28px] py-[1.64px]">
                    <div className="font-['Roboto'] text-[13px] font-normal leading-[18px] tracking-tight text-black/90">
                      Svelte
                    </div>
                  </div>
                </div>
                <div className="absolute left-[317.05px] top-[101.28px] inline-flex items-center justify-start rounded-[54.71px] bg-black/10 px-[4.95px] py-[2.48px]">
                  <div className="inline-flex flex-col items-start justify-start px-[3.28px] py-[1.64px]">
                    <div className="font-['Roboto'] text-[13px] font-normal leading-[18px] tracking-tight text-black/90">
                      Express
                    </div>
                  </div>
                </div>
                <div className="absolute left-[294.15px] top-[79.36px] inline-flex items-center justify-start rounded-[54.71px] bg-black/10 px-[4.95px] py-[2.48px]">
                  <div className="inline-flex flex-col items-start justify-start px-[3.28px] py-[1.64px]">
                    <div className="font-['Roboto'] text-[13px] font-normal leading-[18px] tracking-tight text-black/90">
                      Node.js
                    </div>
                  </div>
                </div>
                <div className="absolute left-[26.41px] top-[116.87px] inline-flex items-center justify-start rounded-[54.71px] bg-black/10 p-[2.19px]">
                  <div className="inline-flex flex-col items-start justify-start px-[4.95px] py-[2.48px]">
                    <div className="font-['Roboto'] text-[13px] font-normal leading-[18px] tracking-tight text-black/90">
                      Angular
                    </div>
                  </div>
                </div>
                <div className="absolute left-[35.38px] top-[164.29px] inline-flex items-center justify-start rounded-[54.71px] bg-black/10 px-[4.95px] py-[2.48px]">
                  <div className="inline-flex flex-col items-start justify-start px-[3.28px] py-[1.64px]">
                    <div className="font-['Roboto'] text-[13px] font-normal leading-[18px] tracking-tight text-black/90">
                      React
                    </div>
                  </div>
                </div>
                <Image
                  height="258"
                  width="258"
                  className="absolute left-[58.01px] top-[1.68px] h-[258.08px] w-[258.08px] rounded-[200px]"
                  src="/images/about-us/Chris Moore.png"
                  alt="Stock photo of smiling man"
                />
                <div className="absolute left-[12.57px] top-[60.33px] inline-flex flex-col items-start justify-start gap-3.5 rounded-xl bg-white p-[9.29px] shadow-xs">
                  <div className="flex flex-col items-start justify-start gap-[4.66px]">
                    <div className="flex flex-col items-start justify-start">
                      <div className="text-right font-['Roboto'] text-sm font-bold leading-[18.68px] text-black/90">
                        Chris Moore
                      </div>
                    </div>
                  </div>
                </div>
                <div className="absolute left-[250.71px] top-[14.86px] h-[49.52px] w-[49.52px] rounded-full bg-primary-light" />
                <div className="absolute left-[260px] top-[24.14px] inline-flex h-[30.95px] w-[30.95px] items-center justify-center">
                  <div className="relative flex h-[30.95px] w-[30.95px] flex-col items-start justify-start">
                    <svg
                      width="32"
                      height="32"
                      viewBox="0 0 32 32"
                      fill="none"
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path
                        d="M26.4601 8.65576L12.2736 22.8423L5.8252 16.3939"
                        stroke="var(--primary-main)"
                        strokeWidth="5.72221"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </div>
                </div>
                <div className="absolute left-[110.81px] top-[246.88px] inline-flex h-[30.57px] flex-col items-start justify-start gap-[13.09px] rounded-[10.91px] bg-white/25 p-[9.29px] shadow-xs backdrop-blur-[24.76px]">
                  <div className="flex flex-col items-start justify-start gap-[4.36px]">
                    <div className="flex flex-col items-start justify-start">
                      <div className="text-center font-['Roboto'] text-[8.73px] font-normal leading-3 text-black/90">
                        Software developer intern at CFA
                      </div>
                    </div>
                  </div>
                </div>
                <div className="absolute left-[241.20px] top-[171.43px] inline-flex flex-col items-start justify-start gap-[11.18px] rounded-[9.31px] bg-white/50 p-[9.29px] shadow-xs backdrop-blur-[24.76px]">
                  <div className="flex flex-col items-start justify-start gap-[3.73px]">
                    <div className="inline-flex items-center justify-start">
                      <div className="flex h-[9.90px] w-[9.90px] items-center justify-center">
                        <div className="inline-flex h-[9.90px] w-[9.90px] items-center justify-center">
                          <div className="relative flex h-[9.90px] w-[9.90px] flex-col items-start justify-start" />
                        </div>
                      </div>
                      <div className="text-center font-['Roboto'] text-[11.18px] font-medium leading-[14.91px] text-black/90">
                        Add Work Experience
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <h4 className="pt-[40px] text-[44px] capitalize leading-[52.80px] text-blue-text2">
                Digital Hiring Tools
              </h4>
              <p>
                Employers and industry partners gain access to our Talent Finder
                Portal.
              </p>
            </div>
          </div>
        </section>
      </section>
      {/*<section className="mx-auto max-w-[1235px] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800">*/}
      {/*  <TrainingProviderMembers></TrainingProviderMembers>*/}
      {/*</section>*/}
      <section
        className="box-border space-y-[68px] bg-white px-[1em] pb-[34px] pt-[54px] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800"
        id="about-us-industry-committee"
      >
        <div className="mx-auto block max-w-[1305px] items-center laptop:flex laptop:gap-x-[50px]">
          <div className="space-y-[20px]">
            <header>
              <h2 className="font-semibold uppercase leading-snug">
                Coalition{" "}
                <b className="text-fluid-lg leading-fluid-lg-snug block pt-[20px] font-normal capitalize text-blue-textdark2">
                  <span className="inline laptop:block">Industry</span>{" "}
                  Committee
                </b>
              </h2>
            </header>
            <p>
              As a member of the Industry Committee, you will play a critical
              role in informing curriculum in collaboration with other employers
              to ensure it stays relevant and effectively prepares students for
              the workforce. Currently, the Industry Committee is prioritizing
              these essential roles across all sectors:
            </p>
            <blockquote className="text-center">
              Software Development | Cybersecurity | IT/Cloud Support | Data
              Analytics
            </blockquote>
            <p>
              With guidance from AWS, Accenture, Microsoft and WTIA, this
              committee proactively collaborates with the Education Committee
              ensuring key industry trends are considered and addressed by
              educators. Quarterly meetings: January, April, July, and October.
            </p>
            <div className="pt-[40px]">
              <RoundedButton
                content="Join"
                link="/join"
                invertColor
                snug
                newColors
                bold={false}
                className="capitalize"
              />
            </div>
          </div>
          <Image
            src="/images/about-us/pexels-gabby-k-9480118.jpg"
            width={650}
            height={650}
            alt="Stock photo of two women and a man collaborating around a table using their paper and electronic notebooks"
            className="mx-auto w-full max-w-[650px]"
          />
        </div>
      </section>
      <section
        className="box-border space-y-[68px] bg-white px-[1em] pb-[34px] pt-[54px] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800"
        id="about-us-education-committee"
      >
        <div className="mx-auto block max-w-[1305px] items-center laptop:flex laptop:gap-x-[50px]">
          <Image
            src="/images/about-us/pexels-fauxels-3184303 1.jpg"
            width={650}
            height={650}
            alt="Stock photo of two women and a man around a table where the man and one of the women are collaborating using their paper notebooks"
            className="mx-auto w-full max-w-[650px]"
          />
          <div className="space-y-[20px]">
            <header>
              <h2 className="font-semibold uppercase leading-snug">
                Coalition{" "}
                <b className="text-fluid-lg leading-fluid-lg-snug block pt-[20px] font-normal capitalize text-blue-textdark2">
                  <span className="inline laptop:block">Education</span>{" "}
                  Committee
                </b>
              </h2>
            </header>
            <p>
              Discover the essential skills for tomorrow's workforce. Our
              Coalition connects you directly with employers, providing valuable
              insights into in-demand skills to help align your curriculum with
              the latest industry standards. Equip your students for success and
              get them HIRED!
            </p>
            <p>Quarterly meetings: February, May, August, November.</p>
            <div className="pt-[40px]">
              <RoundedButton
                content="Join"
                link="/join"
                invertColor
                snug
                newColors
                bold={false}
                className="capitalize"
              />
            </div>
          </div>
        </div>
      </section>
      <section className="mx-auto mt-[72px] box-border max-w-[1235px] px-[1em] text-left font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800">
        <h2 className="mb-[48px] text-center text-[44px] capitalize leading-[52.80px] text-blue-textdark2">
          Structure &amp; Governance
        </h2>
        <div className="block laptop:flex laptop:gap-x-[50px]">
          <div className="flex-1 space-y-[10px]">
            <h3 className="text-center text-[44px] capitalize leading-[52.80px] text-blue-text2">
              Steering Committee
            </h3>
            <p>
              Executives from AWS and Accenture co-lead this committee,
              providing credibility, prioritization and policy for the Coalition
              and its initiatives.
            </p>
          </div>
          <div className="flex-1 space-y-[10px]">
            <h3 className="text-center text-[44px] capitalize leading-[52.80px] text-blue-text2">
              Member Committees
            </h3>
            <p>
              Function-based committees that set the agenda for specific
              interests among membership groups such as employers and educators.
            </p>
          </div>
          <div className="flex-1 space-y-[10px]">
            <h3 className="text-center text-[44px] capitalize leading-[52.80px] text-blue-text2">
              <span className="inline laptop:block">At-large</span> Members
            </h3>
            <p>
              Organizations and individuals active in networking and utilizing
              the Coalition&apos;s resources.
            </p>
          </div>
        </div>
        <section className="mx-auto mt-[68px] max-w-[1235px] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800">
          <h3 className="text-center text-[22px] font-semibold uppercase leading-[30.80px] text-blue-textdark2">
            Co-Leadership Partners
          </h3>
          <div className="mb-[108px] mt-[20px] flex flex-wrap items-center justify-center gap-x-[100px] gap-y-[50px] py-[10px]">
            <Image
              height="82"
              width="395"
              className="max-w-[395px]"
              src="/images/training-providers/WTIA.png"
              alt="Washington Technology Industry Association (WTIA) Logo"
            />
          </div>
        </section>
      </section>
      <section className="mx-auto mb-[92.6px] box-border max-w-[1235px] px-[1em] font-['Roboto'] text-[22px] font-normal leading-[30.80px] text-gray-800">
        <h2 className="my-[48px] text-center text-[44px] capitalize leading-[52.80px] text-blue-textdark2">
          Washington Tech Workforce Coalition Funding &amp; Management
        </h2>
        <div className="block text-left laptop:flex laptop:gap-x-[70px]">
          <div className="flex-1 space-y-[10px]">
            <Image
              height="90"
              width="233"
              className="mx-auto max-w-[233px]"
              src="/images/training-providers/career-connect-wa.png"
              alt="Career Connect Washington Logo"
            />
            <p>
              Initial funding for the Coalition is from the US Department of
              Commerce Good Jobs Challenge grant through the Washington Jobs
              Initiative managed by Washington Student Achievement Council.
            </p>
          </div>
          <div className="flex-1 space-y-[10px]">
            <Image
              height="90"
              width="182"
              className="mx-auto max-w-[182px]"
              src="/images/CFA logo stacked.svg"
              alt="Computing For All Logo"
            />
            <p>
              <Link
                href="https://www.comptingforall.org/"
                target="_blank"
                className="underline"
              >
                Computing for All
              </Link>
              , a 501(c)(3) technology education nonprofit organization based in
              Seattle, Washington, has trained diverse, low-income high school
              and college students for more than five years. In its role as the
              Washington State IT and Cybersecurity Sector Intermediary and
              backbone operator for the WJI grant, it manages the Tech Workforce
              Coalition.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
