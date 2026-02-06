"use client";

import { Box, Container, Typography } from "@mui/material";
import Grid from "@mui/material/Grid";

import Link from "next/link";
import Image from "next/image";

const footerData = [
  {
    title: "Coalition",
    links: [
      { label: "Home", href: "/" },
      { label: "About Us", href: "/about-us" },
      // { label: "Events", href: "/services/events" },
      // {
      //   label: "Community Network",
      //   href: "https://forum.watechwfcoalition.org/",
      // },
    ],
  },
  {
    title: "For Employers",
    links: [
      // {
      //   label: "Search for Talent",
      //   href: "/employers/dashboard/talent-search",
      // },
      { label: "See the Value", href: "/services/employers" },
      { label: "Join the Coalition", href: "/join" },
    ],
  },
  {
    title: "For Job Seekers",
    links: [
      // { label: "Career Services", href: "/services/careers" },
      { label: "Learn More & Join", href: "/services/jobseekers" },
      // {
      //   label: "Community Network",
      //   href: "https://forum.watechwfcoalition.org/",
      // },
      { label: "Search for Jobs", href: "/services/joblistings" },
      { label: "Career Paths", href: "/services/careers" },
      // { label: "Attend an Event", href: "/services/events" },
    ],
  },
  {
    title: "For Educators",
    links: [
      { label: "Join the Coalition", href: "/join" },
      { label: "Partners", href: "/services/training-providers" },
    ],
  },
];

export default function SitemapFooter() {
  return (
    <>
      <Box sx={{ backgroundColor: "secondary.main", color: "white", py: 6 }}>
        <Container maxWidth="lg">
          <Grid
            container
            spacing={4}
            sx={{
              justifyContent: "left",
              alignItems: "flex-start",
              textAlign: "left",
            }}
          >
            <Grid size={{ xs: 12, sm: 2, lg: 1 }}>
              <Link href="/">
                <span className="sr-only">Tech Workforce Coalition</span>
                <Image
                  src="/images/TWC-alt-white.svg"
                  alt="Tech Workforce Coalition"
                  width={69}
                  height={27.24}
                />
              </Link>
            </Grid>
            <Grid container spacing={16}>
              {footerData.map((section) => (
                <Grid
                  size={{ xs: 12, sm: 5, md: 4, lg: 3 }}
                  key={section.title}
                >
                  <Typography
                    fontWeight="bold"
                    style={{
                      marginBottom: "1.5rem",
                      color: "inherit",
                      fontSize: "1rem",
                      lineHeight: "150%",
                      letterSpacing: "0.15px",
                    }}
                    gutterBottom
                  >
                    {section.title}
                  </Typography>
                  {section.links.map((link) => (
                    <Link
                      key={link.label}
                      href={link.href}
                      style={{
                        display: "block",
                        marginBottom: "1.5rem",
                        color: "inherit",
                        fontSize: "1rem",
                        lineHeight: "150%",
                        letterSpacing: "0.15px",
                      }}
                    >
                      {link.label}
                    </Link>
                  ))}
                </Grid>
              ))}
            </Grid>
          </Grid>
        </Container>
      </Box>

      <Grid
        container
        spacing={3}
        sx={{
          width: "100%",
          maxWidth: "1370px",
          py: "12px",
          px: { xs: 2, md: 3, xl: 0 },
          mx: "auto",
          flexWrap: "wrap",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <Grid
          size={{
            xs: 12,
            sm: "auto",
          }}
          sx={{
            display: "flex",
            flexDirection: { xs: "column", sm: "row" },
            alignItems: { xs: "flex-start", sm: "center" },
            py: "8px",
            gap: 3,
          }}
        >
          <Link href="/policies/terms-of-service" style={{ color: "inherit" }}>
            Terms of Services
          </Link>
          <Link href="/policies/privacy-policy" style={{ color: "inherit" }}>
            Privacy Policy
          </Link>
          <Link
            href="https://form.asana.com/?k=YUsxTQ4kvMZCAIN2QbO7Gg&d=1207928585647173"
            style={{ color: "inherit" }}
          >
            Report An Issue
          </Link>
        </Grid>

        <Grid
          size={{
            xs: 12,
            sm: "auto",
          }}
          sx={{
            display: "flex",
            justifyContent: "flex-end",
            alignItems: "center",
          }}
        >
          <a
            href="https://www.linkedin.com/company/washington-tech-workforce-coalition"
            target="_blank"
            rel="noopener noreferrer"
            style={{
              color: "inherit",
              display: "flex",
              alignItems: "center",
              gap: "8px",
            }}
          >
            <p style={{ margin: 0 }}>Follow Us:</p>
            <Image
              src="/images/stock/linkedin-black.png"
              alt="Linkedin Link"
              width={22}
              height={22}
            />
          </a>
        </Grid>
      </Grid>
    </>
  );
}
