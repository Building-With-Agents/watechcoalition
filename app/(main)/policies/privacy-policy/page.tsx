import {
  Box,
  Container,
  Typography,
  Link,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

export default function PrivacyPolicyPage() {
  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        {/* Main Title */}
        <Typography
          variant="h3"
          component="h1"
          align="center"
          gutterBottom
          sx={{ fontWeight: "bold" }}
        >
          Washington Tech Workforce Coalition Privacy Policy
        </Typography>

        {/* Last Updated */}
        <Typography align="center" sx={{ mb: 2 }}>
          Last Updated: February 27, 2025
        </Typography>

        {/* Introduction */}
        <Typography>
          This privacy policy ("Privacy Policy") explains how Washington Tech
          Workforce Coalition, a program of Computing for All ("we", "our", or
          "us") uses the information you (“You” or “user”) provide by use of the
          website located at{" "}
          <Link href="https://www.watechcoalition.org">
            www.watechcoalition.org
          </Link>{" "}
          and any services offered through it (the "Site"). By using this Site,
          you acknowledge that you have read, understand, and agree to the
          Privacy Policy. We update our Privacy Policy periodically to ensure
          that our Privacy Policy continues to clearly explain how we collect
          and use personal and non-personal data.
        </Typography>

        <Typography>
          Computing For All reserves the right to amend this Privacy Policy at
          any time.
        </Typography>

        <Typography>
          This Privacy Policy describes, in a comprehensive manner, how we use
          your data.
        </Typography>

        <Typography>
          You may exercise any of the rights described in this policy or ask
          questions by contacting us at:{" "}
          <Link href="mailto:Ritu@computingforall.org">
            Ritu@computingforall.org
          </Link>
        </Typography>

        {/* What we collect */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          What we collect
        </Typography>

        <Typography>This policy applies to information we collect:</Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="On this Website." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="In e-mail, text, and other electronic messages between you and this Site." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Through any forms, submissions, or surveys (the “Your Submissions”) filled out by you on the Site." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Any demographic information." />
          </ListItem>
        </List>

        <Typography>It does not apply to information collected by:</Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="us offline or through any other means, including on any other website operated by Computing For All or any third party including our subsidiaries or affiliates;" />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="any third party (including our affiliates and subsidiaries), including through any application or content (including advertising) that may link to or be accessible from or on the Site." />
          </ListItem>
        </List>

        <Typography>
          Please read this policy carefully to understand our policies and
          practices regarding your information and how we will treat it. If you
          do not agree with our policies and practices, your choice is not to
          use our Site. By accessing or using this Site, you agree to this
          privacy policy. This policy may change from time to time, so please
          check the policy periodically for updates.
        </Typography>

        {/* Information collected */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Information collected
        </Typography>

        <Typography>
          We collect several types of information from and about users of our
          Site, including information:
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary='by which you may be personally identified, such as name, postal address, zip code, e-mail address, IP address, current employer, employment history, educational history, and telephone number. ("personal information");' />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="that is about you but individually does not identify you, such information is generally compiled and anonymized information;" />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="that you provide by filling in forms or uploading content to our Site. This includes information provided at the time of registering to use our Site or subscribing to our service. We may also ask you for information when you report a problem with our Site or e-mail us with questions or feedback;" />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="records and copies of your correspondence (including e-mail addresses), if you contact us;" />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="responses to surveys that we might ask you to complete for research purposes; and" />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="information about your internet connection, the equipment you use to access our Site, and usage details." />
          </ListItem>
        </List>

        <Typography>We collect this information:</Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="directly from you when you provide it to us." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="automatically as you navigate through the site. Information collected automatically may include usage details, IP addresses and information collected through cookies, web beacons, and other tracking technologies." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="from third parties, for example, our business partners." />
          </ListItem>
        </List>

        {/* Information collected directly from you */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Information collected directly from you
        </Typography>

        <Typography>
          You also may provide information to be published or displayed
          (hereinafter, "posted") on public areas of the Site, or transmitted to
          other users of the Website or third parties (collectively, "User
          Contributions"). Your User Contributions are posted on and transmitted
          to others at your own risk. Although we limit access to certain pages,
          you may set privacy settings for such information by logging into your
          account profile. Please be aware that no security measures are perfect
          or impenetrable. Additionally, we cannot control the actions of other
          users of the Site with whom you may choose to share your User
          Contributions. Therefore, we cannot and do not guarantee that your
          User Contributions will not be viewed by unauthorized persons.
        </Typography>

        {/* Automatic Data Collection */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Information We Collect Through Automatic Data Collection Technologies
        </Typography>

        <Typography>
          While most of the data comes directly from you, as you navigate
          through and interact with our Site, we may use automatic data
          collection technologies to collect certain information about your
          equipment, browsing actions, and patterns, including:
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Details of your visits to our Site, including traffic data, location data, logs, and other communication data and the resources that you access and use on the Website." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Information about your computer and internet connection, including your IP address, operating system, and browser type." />
          </ListItem>
        </List>

        <Typography>
          We do not track our users over time and across third party websites to
          provide targeted advertising and therefore do not respond to DO NOT
          TRACK (DNT) signals. However, some third-party sites do keep track of
          your browsing activities when serving you content. If you are visiting
          such sites, most browsers allow you to set the DNT signal so that
          third parties are notified that you do not want to be tracked.{" "}
          <Link
            href="https://support.google.com/chrome/answer/114662?hl=en"
            target="_blank"
          >
            Google DNT Support Page
          </Link>
          ,{" "}
          <Link
            href="https://support.apple.com/guide/safari/manage-cookies-sfri11471/mac"
            target="_blank"
          >
            Apple DNT Support Page
          </Link>
        </Typography>

        <Typography>
          Some of the information we collect automatically is statistical data
          and does not include personal information, but we may maintain it or
          associate it with personal information we collect in other ways or
          receive from you or third parties. It helps us improve our Site and
          deliver a better, more personalized service, including by enabling us
          to:
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Estimate our audience size and usage patterns." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Store information about your preferences, allowing us to customize our Site according to your individual interests." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Speed up your searches." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Recognize you when you return to our Site." />
          </ListItem>
        </List>

        <Typography>
          The technologies we use for this automatic data collection may
          include:
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Cookies (or browser cookies). A cookie is a small file placed on the hard drive of your computer. You may refuse to accept browser cookies by activating the appropriate setting on your browser. However, if you select this setting you may be unable to access certain parts of our Site. Unless you have adjusted your browser setting so that it will refuse cookies, our system will issue cookies when you direct your browser to our Site. You may disable cookies at any time." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Web Beacons. Our Site may use web beacons (also known as pixel tags or clear GIFs), which are small, invisible images or pieces of code embedded in our pages or emails. These web beacons help us understand how users interact with our content, such as tracking when an email is opened or when a specific page is visited. This information is used to improve our services, monitor marketing campaign effectiveness, and enhance user experience. Web beacons do not collect personal information directly but may be used in conjunction with other tracking technologies like cookies." />
          </ListItem>
        </List>

        {/* How We Use Your Information */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          How We Use Your Information
        </Typography>

        <Typography>
          We use information that we collect about you or that you provide to
          us, including any personal information:
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="To present our Website and its contents to you." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To provide you with information about employment opportunities." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To provide you with information about job seekers." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="We may use and disclose your personal information for operational purposes. The uses and disclosures are necessary to efficiently and effectively run this Website and offer you services." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To create new features." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To provide you with information, products or services that you request from us." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To carry out our obligations and enforce our rights arising from any contracts entered into between you and us. Under certain circumstances, we may use and disclose personal information about you as required by our grants and fiscal sponsorship agreements. When this occurs, we will take steps to protect your privacy." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To notify you about changes to our Site or any products or services we offer or provide through it." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To allow you to participate in interactive features on our Site." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="In any other way we may describe when you provide the information." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="For any other purpose with your consent." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To fulfill any other purpose for which you provide it." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To contact you." />
          </ListItem>
        </List>

        {/* Disclosure of Your Information */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Disclosure of Your Information
        </Typography>

        <Typography>
          We may disclose aggregated information about our users, and
          information that does not identify any individual, without
          restriction.
        </Typography>

        <Typography>
          We may disclose personal information that we collect or you provide as
          described in this privacy policy:
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="To our subsidiaries and affiliates." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To contractors, service providers and other third parties we use to support our business and who are bound by contractual obligations to keep personal information confidential and use it only for the purposes for which we disclose it to them." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To third parties for their review. For example, we may disclose information about job seekers to potential employers that have access to the Site; or, about employers to job seekers looking for gainful employment. Please note these third parties may choose to share your profile with additional parties, and we are not responsible for the way that information is used." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To a buyer or other successor in the event of a merger, divestiture, restructuring, reorganization, dissolution or other sale or transfer of some or all of Computing For All’s assets, whether as a going concern or as part of bankruptcy, liquidation or similar proceeding, in which personal information held by Computing For All about our Website users is among the assets transferred." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="For any other purpose disclosed by us when you provide the information." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To comply with any court order, law or legal process, including to respond to any government or regulatory request." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To screen for and prevent undesirable or abusive activities." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To prevent potentially illegal activities." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="To enforce or apply our Terms and Conditions." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="If we believe disclosure is necessary or appropriate to protect the rights, property, or safety of Computing For All, our customers or others. This includes exchanging information with other companies and organizations for the purposes of fraud protection and credit risk reduction." />
          </ListItem>
        </List>

        {/* Choices About How We Use and Disclose Your Information */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Choices About How We Use and Disclose Your Information
        </Typography>

        <Typography>
          We strive to provide you with choices regarding the personal
          information you provide to us. We have created mechanisms to give you
          the following control over your information:
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Tracking Technologies and Advertising. You can set your browser to refuse all or some browser cookies, or to alert you when cookies are being sent. To learn how you can manage your Flash cookie settings, visit the Flash player settings page on Adobe's website. If you disable or refuse cookies, please note that some parts of this site may then be inaccessible or not function properly." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="We do not control third parties' collection or use of your information to serve interest-based advertising. However, these third parties may provide you with ways to choose not to have your information collected or used in this way. You can opt out of receiving targeted ads from members of the Network Advertising Initiative (NAI) on the NAI's website." />
          </ListItem>
        </List>

        {/* Accessing and Correcting Your Information */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Accessing and Correcting Your Information
        </Typography>

        <Typography>
          We strive to give you autonomy over your personal information.
          Therefore, there are several ways for you to access or request changes
          or deletion of your personal information.
        </Typography>

        <Typography>
          Note: We may not accommodate a request to change information if we
          believe the change would violate any law or legal requirement or cause
          the information to be incorrect.
        </Typography>

        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Delete Data: You can ask us to erase or delete all or some of your personal data (e.g., if it is no longer necessary to provide services to you). If you request that any of your personal data be deleted, we reserve the right to terminate and/or limit your access to the service to the extent services cannot be reasonably provided without that information." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Change or Correct Data: You can edit some of your personal data through your account. You can also ask us to change, update, or fix your data, particularly if it is inaccurate." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Object to, or Limit or Restrict, Use of Data: You can ask us to stop using all or some of your personal data (e.g., if we have no legal right to keep using it) or to limit our use of it (e.g., if your personal data is inaccurate or unlawfully held). Please understand that if your personal data has been anonymized or archived, we reserve the right to freely use that information." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Right to Access and/or Take Your Data: You can ask us for a copy of your personal data and request it in machine-readable form." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Refuse Cookies: You can set your browser to refuse all or some cookies, or to alert you when cookies are being sent. If you disable or refuse cookies, please note that some parts of this Site may not function properly." />
          </ListItem>
        </List>

        {/* Children Under the Age of 18 */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Children Under the Age of 18
        </Typography>

        <Typography>
          Our Site is not intended for children under 18 years of age. No one
          under age 18 may provide any personal information to or on the Website
          or through any forms and submissions. We do not knowingly collect
          personal information from children under 18. If you are under 18, do
          not use or provide any information on this Site or through any of its
          features, including registration, interactive, or public comment
          features. If we learn we have collected or received personal
          information from a child under 18 without verification of parental
          consent, we will delete that information. If you believe we might have
          any information from or about a child under 18, please contact us at{" "}
          <Link href="mailto:Ritu@computingforall.org">
            Ritu@computingforall.org
          </Link>
          .
        </Typography>

        {/* Your California Privacy Rights */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Your California Privacy Rights
        </Typography>

        <Typography>
          Computing For All and Washington Tech Workforce Coalition operate in
          Washington. However, if you are a California resident, you should be
          aware of California Civil Code Section § 1798.83, which permits users
          of our Site that are California residents to request disclosure about
          the personal information we collect and details about how we collect,
          use, and disclose your personal information. California residents also
          have the right to request that we delete, erase, or update personal
          information under certain circumstances. Furthermore, all California
          residents have the right to opt out of the sale of personal
          information. To make such a request, please send an e-mail to{" "}
          <Link href="mailto:Ritu@computingforall.org">
            Ritu@computingforall.org
          </Link>{" "}
          or write us at:
          <br />
          Computing for All
          <br />
          1311 108th Ave NE
          <br />
          Bellevue, WA 98004.
        </Typography>

        {/* Data Security */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Data Security
        </Typography>

        <Typography>
          We have implemented reasonable measures designed to secure your
          personal information from accidental loss and from unauthorized
          access, use, alteration, and disclosure.
        </Typography>

        <Typography>
          Unfortunately, the transmission of information via the internet is not
          completely secure. Although we do our best to protect your personal
          information, we cannot guarantee the security of information
          transmitted to our Site. Any transmission of personal information is
          at your own risk. We are not responsible for circumvention of any
          privacy settings or security measures contained on the Site.
        </Typography>

        {/* Consent to Processing */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Consent to Processing
        </Typography>

        <Typography>
          The Site is hosted and operated in the United States in accordance
          with U.S. law. We make no representation that the Site is governed by
          or operated in accordance with the laws of any other nation. If you
          are located in the European Union, Canada, or elsewhere outside of the
          United States, please be aware that information we collect may be
          transferred to and processed in the United States. By using the Site,
          or providing us with any information, you (a) acknowledge that the
          Website is subject to the laws of the United States, (b) consent to
          the collection, processing, maintenance, and transfer of such
          information in and to the United States and other applicable
          territories where privacy laws may not be as comprehensive as or
          equivalent to those in your country, and (c) waive any claims that may
          arise under those laws.
        </Typography>

        {/* Changes to Our Privacy Policy */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Changes to Our Privacy Policy
        </Typography>

        <Typography>
          We may amend this Privacy Policy from time to time to ensure
          compliance with the law or reflect changes in how we operate our Site.
          Users will be notified of significant changes via email or through a
          notice posted on our Site.
        </Typography>

        {/* Contact Information */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Contact Information
        </Typography>

        <Typography>
          To ask questions or comment about this privacy policy and our privacy
          practices, contact us at:
        </Typography>
        <Link href="mailto:Ritu@computingforall.org">
          Ritu@computingforall.org
        </Link>
        <Typography>Computing for All</Typography>
        <Typography>1311 108th Ave NE, Bellevue, WA 98004</Typography>
      </Box>
    </Container>
  );
}
