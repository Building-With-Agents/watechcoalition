import {
  Box,
  Container,
  Typography,
  Link,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

export default function page() {
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
          Terms and Conditions
        </Typography>

        {/* Effective Date */}
        <Typography align="center" sx={{ mb: 2 }}>
          <Box component="span" sx={{ fontWeight: "bold" }}>
            Effective Date: December 3, 2024
          </Box>
        </Typography>

        {/* Introduction */}
        <Typography>
          These Terms and Conditions ("Terms") govern your (“You” or “user”) use
          of the website located at{" "}
          <Link href="https://www.watechcoalition.org">
            www.watechcoalition.org
          </Link>{" "}
          and any services offered through ("Site"), which is owned and operated
          by the Washington Tech Workforce Coalition ("we", "our", or "us"). By
          using this Site, you acknowledge that you have read, understand, and
          agree to abide by these Terms.
        </Typography>

        {/* Services */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Services
        </Typography>
        <Typography>
          We provide the following services to job seekers: connecting them to
          training providers to increase their job-readiness in the IT industry
          and connecting them with potential employers in IT-related job roles.
          Job seekers understand that Computing For All does not post any roles
          and is not responsible for any content posted by a third party.
          Further, any job listings are simply invitations to apply for a role
          and do not guarantee, either implicitly or explicitly, any employment
          with any employer.
        </Typography>
        <Typography>
          We provide the following services to employers: connecting employers
          with training partners and job seekers to help you find potential
          employees with the skills you require; and, facilitating communication
          between employers, training providers, and job seekers. Employers
          understand that Computing For All does not control the responses the
          employers receive for their job postings and is not responsible for
          any content posted by a third party. Further, any responses are not
          pre-screened, filtered, or edited in any way for any purpose and the
          responses do not guarantee or warrant, either implicitly or
          explicitly, the content of the responses or type of employee, should
          an individual be hired.
        </Typography>
        <Typography>
          We do not supply any goods or services, other than outlined above.
        </Typography>

        {/* Accessing the Website and Account Security */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Accessing the Website and Account Security
        </Typography>
        <Typography>
          We reserve the right to withdraw or amend the Site, and any service or
          material provided on the Site, in our sole discretion, without notice.
          We will not be liable if for any reason all or any part of the Website
          is unavailable at any time or for any period. From time to time, we
          may restrict access to some parts of the Site, or the entire Site, to
          users, including registered users.
        </Typography>
        <Typography>
          You are responsible for making all arrangements necessary for you to
          have access to the Site and that you, or anyone you allow, is
          compliant with these Terms.
        </Typography>
        <Typography>
          To access the Site or some of the resources it offers, you may be
          asked to provide certain registration details or other information. It
          is a condition of your use of the Site that all information you
          provide is correct, current, and complete. You agree that all
          information you provide to register with this Site or otherwise,
          including but not limited to through the use of any interactive
          features on the Site, is governed by our{" "}
          <Link href="/policies/privacy-policy">Privacy Policy</Link>, and you
          consent to all actions we take with respect to your information
          consistent with our Privacy Policy.
        </Typography>
        <Typography>
          If you choose, or are provided with, a username, password or any other
          piece of information as part of our security procedures, you must
          treat such information as confidential, and you must not disclose it
          to any other person or entity. You also acknowledge that your account
          is personal to you and agree not to provide any other person with
          access to the Site or portions of it using your username, password or
          other security information. We use OAuth 2.0 for account
          authentication, and support providers such as Google, Microsoft Entra,
          and GitHub. For information on how we use this, please see our{" "}
          <Link href="/policies/privacy-policy">Privacy Policy</Link>. You agree
          to notify us immediately of any unauthorized access to or use of your
          username, password, or any other breach of security. You also agree to
          ensure that you exit your account at the end of each session.
        </Typography>
        <Typography>
          We reserve the right to suspend or terminate your account if we
          believe you are using our Site unlawfully or violating these Terms. We
          also have the right to disable any username, password, or other
          identifier, whether chosen by you or provided by us, at any time in
          our sole discretion for any or no reason, including if, in our
          opinion, you have violated any provision of these Terms of Use.
        </Typography>

        {/* Intellectual Property */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Intellectual Property
        </Typography>
        <Typography
          variant="h6"
          component="h6"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Content owned by Us
        </Typography>
        <Typography>
          The Site and its contents, features and functionality (including but
          not limited to all information, software, text, displays, images,
          video and audio, and the design, selection and arrangement thereof),
          are owned by Computing For All, its licensors, or other providers of
          such material and are protected by copyright, trademark, patent, trade
          secret and other intellectual property or proprietary rights laws.
        </Typography>
        <Typography>
          You must not delete or alter any copyright, trademark or other
          proprietary rights notices from copies of materials from this site.
        </Typography>
        <Typography>
          If you print, copy, modify, download or otherwise use or provide any
          other person with access to any part of the Site in breach of the
          Terms, your right to use the Site will cease immediately and you must,
          at our option, return or destroy any copies you have made. No right,
          title or interest in or to the Site or any content on the Site is
          transferred to you, and all rights not expressly granted are reserved
          by Us. Any use of the Website not expressly permitted by these Terms
          is a breach of these Terms and may violate copyright, trademark and
          other laws.
        </Typography>
        <Typography
          variant="h6"
          component="h6"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Content owned by You
        </Typography>
        <Typography>
          We do not claim ownership of any data, text, information, User
          Contributions (defined below), or materials (“Your Submissions”)
          provided by you. You own all rights to Your Submissions.
        </Typography>
        <Typography>
          As a job seeker you may provide a YouTube video showcasing skills,
          your resume, a cover letter, your work history, and your education
          history. It is your responsibility to ensure that all information
          provided is yours and does not violate any other agreements, including
          other website terms and conditions, or equivalent.
        </Typography>
        <Typography>
          As an employer, you may provide job postings, company profiles, a list
          of the skill requirements, and employment opportunities. By posting on
          the Site, you agree not to post anything illegal, misleading, or that
          violates these Terms or any applicable laws and regulations.
        </Typography>
        <Typography>
          When you submit Your Submissions, you grant Computing For All a
          worldwide, perpetual, non-revocable, sublicensable, transferable
          license to use, distribute, reproduce, modify, adapt, publish,
          translate, archive, publicly perform, and publicly display Your
          Submissions (in whole or in part) in any format or medium now known or
          later developed. You agree and understand that included in the
          aforementioned grant is your right of publicity (right to your name,
          image, likeness, or other state equivalent right, if present), as well
          as copyright, trademark, privacy, or any other proprietary rights.
          Computing For All does not and will not pre-screen Your Submissions.
          You are solely responsible for the information and the accuracy of the
          information in Your Submissions.
        </Typography>

        {/* User Contributions */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          User Contributions
        </Typography>
        <Typography>
          The Site may contain message boards, personal web pages or profiles,
          forums, bulletin boards, event signup, job posts and other interactive
          features (collectively, "Interactive Services") that allow users to
          post, submit, publish, display or transmit to other users or other
          persons (hereinafter, "post") content or materials (collectively,
          "User Contributions") on or through the Site.
        </Typography>
        <Typography>
          All User Contributions must comply with the content standards set out
          in these Terms.
        </Typography>
        <Typography>
          Any User Contribution you post to the Site will be considered
          non-confidential and non-proprietary. By providing any User
          Contribution on the Site, you grant us and our affiliates and service
          providers, and each of their and our respective licensees, successors
          and assigns the right to use, reproduce, modify, perform, display,
          distribute and otherwise disclose to third parties any such material
          for any purpose.
        </Typography>
        <Typography>
          You represent and warrant that you own or control all rights in and to
          the User Contributions and have the right to grant the license granted
          above to us and our affiliates and service providers, and each of
          their and our respective licensees, successors and assigns. All of
          your User Contributions do and will comply with these Terms of Use.
          You understand and acknowledge that you are responsible for any User
          Contributions you submit or contribute, and you, not us, have full
          responsibility for such content, including its legality, reliability,
          accuracy and appropriateness.
        </Typography>
        <Typography>
          We are not responsible, or liable to any third party, for the content
          or accuracy of any User Contributions posted by you or any other user
          of the Website.
        </Typography>

        {/* Monitoring and Enforcement; Termination */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Monitoring and Enforcement; Termination
        </Typography>
        <Typography>
          We have the right to remove or refuse to post any User Contributions
          for any or no reason in our sole discretion.
        </Typography>
        <Typography>
          We may take any action with respect to any User Contribution that we
          deem necessary or appropriate in our sole discretion, including if we
          believe that such User Contribution violates the Terms, including the
          Content Standards, infringes any intellectual property right or other
          right of any person or entity, or threatens the personal safety of
          users of the Site or the public or could create liability for us.
        </Typography>
        <Typography>
          We may disclose your identity or other information about you to any
          third party who claims that material posted by you violates their
          rights, including their intellectual property rights or their right to
          privacy.
        </Typography>
        <Typography>
          We may take appropriate legal action, including without limitation,
          referral to law enforcement, for any illegal or unauthorized use of
          the Site.
        </Typography>
        <Typography>
          We may terminate or suspend your access to all or part of the Site for
          any or no reason, including without limitation, any violation of these
          Terms.
        </Typography>
        <Typography>
          Without limiting the foregoing, we have the right to fully cooperate
          with any law enforcement authorities or court order requesting or
          directing us to disclose the identity or other information of anyone
          posting any materials on or through the Website.
        </Typography>
        <Typography>
          You waive and hold harmless Computing For All and its board members,
          employers, agents, affiliates, licensees and service providers from
          any claims resulting from any action taken by any of the foregoing
          parties during or as a result of its investigations and from any
          actions taken as a consequence of investigations by either such
          parties or law enforcement authorities.
        </Typography>
        <Typography>
          However, we cannot and do not undertake to review all material before
          it is posted on the Site and cannot ensure prompt removal of
          objectionable material after it has been posted. Accordingly, we
          assume no liability for any action or inaction regarding
          transmissions, communications or content provided by any user or third
          party. We have no liability or responsibility to anyone for
          performance or nonperformance of the activities described in this
          section.
        </Typography>

        {/* Content Standards */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Content Standards
        </Typography>
        <Typography>
          These content standards apply to any and all User Contributions and
          use of Interactive Services. User Contributions must in their entirety
          comply with all applicable federal, state, local and international
          laws and regulations. Without limiting the foregoing, User
          Contributions must not:
        </Typography>
        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", marginLeft: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Contain any material which is defamatory, obscene, indecent, abusive, offensive, harassing, violent, hateful, inflammatory or otherwise objectionable." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Promote sexually explicit or pornographic material, violence, or discrimination based on race, sex, religion, nationality, disability, sexual orientation or age." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Infringe any patent, trademark, trade secret, copyright or other intellectual property or other rights of any other person." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Violate the legal rights (including the rights of publicity and privacy) of others or contain any material that could give rise to any civil or criminal liability under applicable laws or regulations or that otherwise may be in conflict with these Terms and our Privacy Policy." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Be likely to deceive any person." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Promote any illegal activity, or advocate, promote or assist any unlawful act." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Cause annoyance, inconvenience or needless anxiety or be likely to upset, embarrass, alarm or annoy any other person." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Impersonate any person, or misrepresent your identity or affiliation with any person or organization." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Give the impression that they emanate from or are endorsed by us or any other person or entity, if this is not the case." />
          </ListItem>
        </List>

        {/* DMCA */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Digital Millennium Copyright Act (DMCA)
        </Typography>
        <Typography>
          We respect the intellectual property rights of others. If you believe
          your copyright in a work has been violated through the Site, content,
          or our services, please provide us with the following information:
        </Typography>
        <Typography>
          Identify the copyrighted work or works that you claim has been
          infringed, or if multiple copyright works are covered by this Notice,
          please provide a representative list of such works.
        </Typography>
        <Typography>
          Identify the material or link you claim is infringing or the subject
          of an infringing activity, that is to be removed or disabled. Please
          provide the URL or the exact location of such infringing materials.
        </Typography>
        <Typography>
          Provide your contact information (Your business name (if applicable),
          your name, address, e-mail address, and phone number).
        </Typography>
        <Typography>
          Include the following statements in the body of the Notice you e-mail
          to us:
        </Typography>
        <Typography>
          “I hereby state that I have a good faith belief that use of
          material(s) in the manner complained of is not authorized by the
          copyright owner, agent, or the law (i.e., fair use). I hereby state
          that the information provided herein is true and accurate, and under
          the penalty of perjury, I am the owner or have been authorized to act
          on behalf of, the owner of the copyright, or the owner of any
          exclusive right that has been allegedly infringed.”
        </Typography>
        <Typography>
          Provide your full legal name and your electronic or physical
          signature.
        </Typography>
        <Typography>
          Deliver this notice with all ancillary documents to:
        </Typography>
        <Typography>
          Copyright Agent <br />
          Apex Law Group PLLC <br />
          Attn: Luis Adan Jimenez <br />
          200 1st Ave W Ste 104 <br />
          Seattle, WA 98119-4291 <br />
          United States <br />
          <Link href="mailto:DMCAAgent@apexlg.org">DMCAAgent@apexlg.org</Link>
        </Typography>

        {/* Trademarks */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Trademarks
        </Typography>
        <Typography>
          Computing For All’s name, the terms Washington Tech Workforce
          Coalition, Computing For All’s logo, and all related names, logos,
          product and service names, designs and slogans are trademarks of
          Computing For All or its affiliates or licensors. You must not use
          such marks without the prior written permission of Computing For All.
          All other names, logos, product and service names, designs and slogans
          on this Site are the trademarks of their respective owners.
        </Typography>

        {/* Reliance on Information Posted */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Reliance on Information Posted
        </Typography>
        <Typography>
          The information presented on or through the Site is made available
          solely for general information purposes. We do not warrant the
          accuracy, completeness or usefulness of this information. Any reliance
          you place on such information is strictly at your own risk. We
          disclaim all liability and responsibility arising from any reliance
          placed on such materials by you or any other visitor to the Site, or
          by anyone who may be informed of any of its contents.
        </Typography>
        <Typography>
          This Site may include content provided by third parties, including
          materials provided by other users, bloggers and third-party licensors,
          syndicators, aggregators and/or reporting services. All statements
          and/or opinions expressed in these materials, and all articles and
          responses to questions and other content, other than the content
          provided by Computing For All, are solely the opinions and the
          responsibility of the person or entity providing those materials.
          These materials do not necessarily reflect the opinion of Computing
          For All. We are not responsible, or liable to you or any third party,
          for the content or accuracy of any materials provided by any third
          parties.
        </Typography>

        {/* Links to Third-Party Websites */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Links to Third-Party Websites
        </Typography>
        <Typography>
          Our Site may contain links to third-party websites or services that we
          do not control. We are not responsible for the content, policies, or
          practices of these third-party websites. You are responsible for
          reviewing the terms and conditions and privacy policies of any
          third-party websites you use.
        </Typography>

        {/* Limitation of Liability */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Limitation of Liability
        </Typography>
        <Typography>
          Computing For All and our directors, officers, agents, employees,
          subsidiaries, and affiliates are not liable for any actions, claims,
          losses, damages, liabilities, or expenses, including legal fees,
          arising from your use of the Site, any websites linked to it, any
          content on the website or such other websites or any services or items
          obtained through the website or such other websites, including any
          direct, indirect, special, incidental, consequential or punitive
          damages, including but not limited to, personal injury, pain and
          suffering, emotional distress, loss of revenue, loss of profits, loss
          of business or anticipated savings, loss of use, loss of goodwill,
          loss of data, and whether caused by tort (including negligence),
          breach of contract or otherwise, even if foreseeable.
        </Typography>
        <Typography>
          The foregoing does not affect any liability which cannot be excluded
          or limited under applicable law.
        </Typography>

        {/* Disclaimer of Warranties */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Disclaimer of Warranties
        </Typography>
        <Typography>
          You understand that we cannot and do not guarantee or warrant that
          files available for downloading from the internet or the Website will
          be free of viruses or other destructive code. You are responsible for
          implementing sufficient procedures and checkpoints to satisfy your
          particular requirements for anti-virus protection and accuracy of data
          input and output, and for maintaining a means external to our site for
          any reconstruction of any lost data.
        </Typography>
        <Typography>
          We will not be liable for any loss or damage caused by a distributed
          denial-of-service attack, viruses or other technologically harmful
          material that may infect your computer equipment, computer programs,
          data or other proprietary material due to your use of the website or
          any services or items obtained through the website or to your
          downloading of any material posted on it, or on any website linked to
          it.
        </Typography>
        <Typography>
          Your use of the Site, its content and any services or items obtained
          through the website is at your own risk. The Site, its content and any
          services or items obtained through the website are provided on an "as
          is" and "as available" basis, without any warranties of any kind,
          either express or implied. Neither Computing For All nor any person
          associated with Computing For All makes any warranty or representation
          with respect to the completeness, security, reliability, quality,
          accuracy or availability of the website. Without limiting the
          foregoing, neither Computing For All nor any person associated with
          Computing For All represents or warrants that the Site, its content or
          any services or items obtained through the website will be accurate,
          reliable, error-free or uninterrupted, that defects will be corrected,
          that our site or the server that makes it available are free of
          viruses or other harmful components or that the Site or any services
          or items obtained through the Site will otherwise meet your needs or
          expectations.
        </Typography>
        <Typography>
          Computing For All hereby disclaims all warranties of any kind, whether
          express or implied, statutory or otherwise, including but not limited
          to any warranties of merchantability, non-infringement and fitness for
          particular purpose.
        </Typography>
        <Typography>
          The foregoing does not affect any warranties which cannot be excluded
          or limited under applicable law.
        </Typography>

        {/* Indemnification */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Indemnification
        </Typography>
        <Typography>
          Except where prohibited by law, you agree to indemnify and hold
          harmless Computing For All, along with our directors, officers,
          agents, employees, subsidiaries, and affiliates, from any actions,
          claims, losses, damages, liabilities, or expenses, including legal
          fees, resulting from your use of our Site, including, but not limited
          to, User Contributions, Your Submissions, or your violation of these
          Terms.
        </Typography>

        {/* Limitation on Time to File Claims */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Limitation on Time to File Claims
        </Typography>
        <Typography>
          Any cause of action or claim you may have arising out of or relating
          to these terms of use or the website must be commenced within one (1)
          year after the cause of action accrues, otherwise, such cause of
          action or claim is permanently barred.
        </Typography>

        {/* Governing Law */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Governing Law
        </Typography>
        <Typography>
          These Terms are governed by the laws of the State of Washington.
        </Typography>

        {/* Severability and Waiver */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Severability and Waiver
        </Typography>
        <Typography>
          If any provision of these Terms is found to be invalid or
          unenforceable under applicable law, such provision will be removed,
          and the remaining provisions will continue in full effect. No waiver
          by Computing For All of any term or condition set forth in these Terms
          shall be deemed a further or continuing waiver of such term or
          condition or a waiver of any other term or condition.
        </Typography>

        {/* Changes to Terms */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Changes to Terms
        </Typography>
        <Typography>
          We may amend these Terms from time to time to ensure compliance with
          the law or reflect changes in how we operate our Site. Users will be
          notified of significant changes via email or through a notice posted
          on our Site.
        </Typography>

        {/* Data Sharing */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Data Sharing
        </Typography>
        <Typography>
          Your Submissions may be shared with our partners. Please see our{" "}
          <Link href="/policies/privacy-policy">Privacy Policy</Link> and{" "}
          <Link href="/policies/user-data-agreement">
            Data Sharing Agreement
          </Link>{" "}
          for more information on how we share your data.
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
          If you have any questions or concerns, please contact us at:
        </Typography>
        <Link href="mailto:Ritu@computingforall.org">
          Ritu@computingforall.org
        </Link>
        <Typography>Computing For All</Typography>
        <Typography>1311 108th Ave NE, Bellevue, WA 98004</Typography>
      </Box>
    </Container>
  );
}
