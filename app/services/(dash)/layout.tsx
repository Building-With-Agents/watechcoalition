"use client";
import Link from "next/link";
import {
  CalendarMonthOutlined,
  LinkedIn,
  LogoutRounded,
  Menu,
  PersonOutlineRounded,
  QuestionAnswerOutlined,
  SearchRounded,
  TaskOutlined,
  WorkOutlineRounded,
} from "@mui/icons-material";
import {
  AppBar,
  Box,
  Drawer,
  Grid,
  IconButton,
  Stack,
  Toolbar,
} from "@mui/material";
import Image from "next/image";
import Avatar from "@/app/ui/components/Avatar";
import { useSession } from "next-auth/react";
import { useCallback, useState } from "react";
import { usePathname } from "next/navigation";
import PillButton from "@/app/ui/components/PillButton";
import Header from "@/app/ui/components/mui/Header";
import Footer from "@/app/ui/Footer";

const drawerWidth = 260;

const employerLinks = [
  {
    href: "/services/employers/dashboard",
    icon: <PersonOutlineRounded />,
    label: "Home",
  },
  {
    href: "/services/employers/dashboard/jobs",
    icon: <WorkOutlineRounded />,
    label: "Jobs",
  },
  {
    href: "/services/employers/dashboard/talent-search",
    icon: <SearchRounded />,
    label: "Search Candidates",
  },
  {
    href: "/services/events/registered",
    icon: <CalendarMonthOutlined />,
    label: "Events",
  },
  {
    href: "https://forum.watechwfcoalition.org/",
    icon: <QuestionAnswerOutlined />,
    label: "Community Network",
    external: true,
  },
];

const jobseekerLinks = [
  {
    href: "/services/jobseekers/dashboard",
    icon: <PersonOutlineRounded />,
    label: "Home",
  },
  {
    href: "/services/joblistings",
    icon: <WorkOutlineRounded />,
    label: "Jobs",
  },
  {
    href: "/services/jobseekers/dashboard/my-applications",
    icon: <TaskOutlined />,
    label: "Applications",
  },
  // {
  //   href: "/services/events/registered",
  //   icon: <CalendarMonthOutlined />,
  //   label: "Events",
  // },
  // {
  //   href: "https://forum.watechwfcoalition.org/",
  //   icon: <QuestionAnswerOutlined />,
  //   label: "Community Network",
  //   external: true,
  // },
];

const UserDrawer = ({
  session,
  links,
  profileLink,
}: {
  session: any;
  links: Array<any>;
  profileLink: string;
}) => {
  const pathname = usePathname();

  return (
    <>
      <Toolbar sx={{ height: "76px" }} />
      <div className="flex flex-col text-button-secondary-idle-text">
        <Stack
          direction="row"
          gap={1}
          sx={{ mt: "25px", alignItems: "center", ml: 5, mb: 3 }}
        >
          <Avatar scale={0.66} imgsrc={session?.user.image || ""} />
          <div>
            <p className="text-wrap font-bold">{session?.user.firstName}</p>
            <Link
              href={profileLink}
              className="text-wrap text-sm text-primary-600 sm-tablet:text-base"
            >
              Edit Profile
            </Link>
          </div>
        </Stack>
        {links.map((link) => (
          <Link
            key={link.label + link.href}
            href={link.href}
            className={`inline-flex items-center justify-start rounded-l-[20px] p-2 ${
              pathname === link.href
                ? "bg-button-secondary-idle-text text-button-secondary-idle-bg"
                : "hover:bg-gray-200"
            }`}
            target={link.external ? "_blank" : undefined}
          >
            <div className="ml-10 space-x-1">
              {link.icon}
              <span>{link.label}</span>
            </div>
          </Link>
        ))}
        <PillButton
          color="inherit"
          startIcon={<LogoutRounded />}
          href="/signout"
          sx={{
            ml: 5,
            mt: 3,
            mb: 3,
            width: "123px",
            color: "secondary.main",
          }}
        >
          Log Out
        </PillButton>
      </div>
    </>
  );
};

export default function Layout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const [mobileOpen, setMobileOpen] = useState(false);
  const handleDrawerToggle = useCallback(
    () => setMobileOpen((prev) => !prev),
    [],
  );

  if (status === "loading") {
    return (
      <div className="min-h-screen">
        {/* Header skeleton */}
        <div className="animate-pulse">
          <div className="h-[76px] border-b bg-white">
            <div className="flex h-full items-center justify-between px-4">
              <div className="h-[50px] w-[75px] bg-gray-200"></div>
            </div>
          </div>
          <div className="flex justify-between">
            <div className="flex-1 p-4"></div>
          </div>
        </div>
      </div>
    );
  }

  if (session?.user.employerId || session?.user.jobseekerId) {
    const isEmployer = !!session?.user.employerId;
    const links = isEmployer ? employerLinks : jobseekerLinks;
    const profileLink = isEmployer
      ? "/edit-profile/employer/profile"
      : "/edit-profile/jobseeker/introduction";

    return (
      <div
        style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}
      >
        <AppBar
          position="sticky"
          variant="outlined"
          color="inherit"
          sx={{ zIndex: 1300, height: "76px", justifyContent: "center" }}
        >
          <Toolbar sx={{ justifyContent: "space-between", zIndex: 20000 }}>
            <Link href="/">
              <span className="sr-only">Tech Workforce Coalition</span>
              <Image
                src="/images/TWC_75x50_2024.svg"
                alt="Tech Workforce Coalition"
                width={75}
                height={50}
              />
            </Link>
            <Stack direction="row">
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ display: { xs: "block", md: "none" } }}
              >
                <Menu />
              </IconButton>
            </Stack>
          </Toolbar>
        </AppBar>
        <Grid sx={{ display: { xs: "none", md: "block" }, width: drawerWidth }}>
          <Drawer
            elevation={0}
            variant="permanent"
            anchor="right"
            sx={{
              display: { xs: "none", md: "block" },
              width: drawerWidth,
              "& .MuiDrawer-paper": { border: 0, width: drawerWidth },
            }}
          >
            <UserDrawer
              session={session}
              links={links}
              profileLink={profileLink}
            />
          </Drawer>
          <Drawer
            variant="temporary"
            anchor="right"
            open={mobileOpen}
            onClose={handleDrawerToggle}
            ModalProps={{ keepMounted: true }}
            sx={{
              display: { xs: "block", md: "none" },
              "& .MuiDrawer-paper": {
                boxSizing: "border-box",
                width: drawerWidth,
              },
            }}
          >
            <UserDrawer
              session={session}
              links={links}
              profileLink={profileLink}
            />
          </Drawer>
        </Grid>
        <Box
          component="main"
          sx={{
            mt: "25px",
            flexGrow: 1,
            width: { md: `calc(100% - ${drawerWidth}px)` },
          }}
        >
          {children}
        </Box>
        <Grid
          gap={2}
          container
          sx={{
            position: "relative",
            alignItems: "center",
            justifyContent: "space-between",
            px: 5,
            py: 2.5,
            zIndex: 1200,
            bgcolor: "neutral.100",
          }}
        >
          <Stack direction={{ xs: "column", sm: "row" }} gap={2}>
            <Link href={"/policies/terms-of-service"}>Terms of Service</Link>
          </Stack>
          <div>
            <p>
              Follow Us{" "}
              <Link
                target="_blank"
                href="https://www.linkedin.com/company/washington-tech-workforce-coalition"
              >
                <LinkedIn />
              </Link>
            </p>
          </div>
        </Grid>
      </div>
    );
  } else {
    return (
      <>
        <Header />
        <div className="grow">{children}</div>
        <Footer />
      </>
    );
  }
}
