import {
  Box,
  Container,
  Typography,
  Link,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";

export default function DataSharingAgreementPage() {
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
          User Data Sharing Agreement
        </Typography>

        {/* Last Updated */}
        <Typography align="center" sx={{ mb: 2 }}>
          Last Updated: February 27, 2025
        </Typography>

        {/* Introduction */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Introduction
        </Typography>
        <Typography>
          This User Data Sharing Agreement ("Agreement") outlines the terms
          under which Washington Tech Workforce Coalition, a program of
          Computing for All, ("we," "us," or "our") collects, uses, shares, and
          protects user data. By using our services, you ("User") agree to the
          terms of this Agreement, which supplements our Privacy Policy and
          Terms and Conditions of Use. In the event of any conflict, this
          Agreement will govern the data-sharing practices.
        </Typography>

        {/* Purpose of Data Sharing */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Purpose of Data Sharing
        </Typography>
        <Typography>
          The primary purpose of collecting and sharing user data is to enhance
          the functionality of our website, including but not limited to:
        </Typography>
        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Connecting job seekers with employers." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Providing tailored job recommendations and career insights." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Enabling third-party services that enhance user experience (e.g., resume-building tools, application tracking systems)." />
          </ListItem>
        </List>

        {/* Types of Data Collected */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Types of Data Collected
        </Typography>
        <Typography>
          We collect and may share the following types of user data:
        </Typography>
        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Personal Identifiable Information (PII): Name, email address, phone number, location, and professional details." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Usage Data: Interaction with our website, search queries, and application activity." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Uploaded Content: Resumes, cover letters, and other documents or information shared by users." />
          </ListItem>
        </List>

        {/* Parties with Whom Data May Be Shared */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Parties with Whom Data May Be Shared
        </Typography>
        <Typography>
          The following data may be shared with the following parties:
        </Typography>
        <List
          disablePadding
          sx={{
            listStyleType: "disc",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Employers and Recruiters: Information such as resumes, education, work history and other various professional details shared explicitly by users seeking job opportunities." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Third-Party Service Providers: Vendors and partners who provide auxiliary services (e.g., payment processors, cloud storage providers) and adhere to strict confidentiality agreements." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Regulatory or Legal Authorities: Data may be disclosed to comply with legal obligations or enforce our rights." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Grant Reporting Requirement: The following data, if applicable, will be collected solely for grant reporting purposes and shared with grant providers: Gender; Veteran Status; Ethnicity; Race; Mental Disability; Personal Address; Company Size; Industry sector; Diversity and inclusion initiatives; and Hiring Statistics." />
          </ListItem>
        </List>

        {/* User Consent */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          User Consent
        </Typography>
        <Typography>
          By creating an account or using our services, you consent to:
        </Typography>
        <List
          disablePadding
          sx={{
            listStyleType: "decimal",
            "& .MuiListItem-root": { display: "list-item", ml: 3 },
          }}
        >
          <ListItem disablePadding>
            <ListItemText primary="Sharing your data with employers and recruiters for job application purposes." />
          </ListItem>
          <ListItem disablePadding>
            <ListItemText primary="Receiving communications from employers, recruiters, and third-party service providers where relevant." />
          </ListItem>
        </List>

        {/* Amendments */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Amendments
        </Typography>
        <Typography>
          We reserve the right to amend this Agreement from time to time to
          reflect changes in our practices, legal obligations, or services.
          Users will be notified of material changes through our website or via
          email, and continued use of the site constitutes acceptance of the
          updated Agreement.
        </Typography>

        {/* Contact Us */}
        <Typography
          variant="h5"
          component="h5"
          gutterBottom
          sx={{ mt: 2, fontWeight: "bold" }}
        >
          Contact Us
        </Typography>
        <Typography>
          To ask questions or comment about this Agreement and our data-sharing
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
