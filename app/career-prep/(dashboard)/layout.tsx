"use client";
import "@/app/ui/admin.css";
import Link from "next/link";
import EditCalendarIcon from "@mui/icons-material/EditCalendar";
import PostAddOutlinedIcon from "@mui/icons-material/PostAddOutlined";
import UpdateOutlinedIcon from "@mui/icons-material/UpdateOutlined";
import {
  ArticleOutlined,
  AssignmentOutlined,
  CalendarMonthOutlined,
  LogoutRounded,
  Menu,
  //NotificationsOutlined,
  PersonOutlineRounded,
  SearchRounded,
  TaskOutlined,
  WorkOutlineRounded,
} from "@mui/icons-material";
import { AppBar, Box, Drawer, IconButton, Stack, Toolbar } from "@mui/material";
import Image from "next/image";
import Avatar from "@/app/ui/components/Avatar";
import { useSession } from "next-auth/react";
import { useCallback, useState } from "react";
import { usePathname } from "next/navigation";
import PillButton from "@/app/ui/components/PillButton";
import AccountMenu from "@/app/ui/components/mui/AccountMenu";

const drawerWidth = 260;

const CareerNavDrawer = ({ session }: { session: any }) => {
  const pathname = usePathname();

  const links = [
    {
      href: "/career-prep",
      icon: <PersonOutlineRounded />,
      label: "Home",
    },
    {
      href: "/career-prep/power-bi",
      icon: <ArticleOutlined />,
      label: "Dynamics Data",
    },
    {
      href: "/career-prep/talent-search",
      icon: <SearchRounded />,
      label: "Talent Search",
    },
    {
      href: "/career-prep/my-case-load",
      icon: <WorkOutlineRounded />,
      label: "My Case Load",
    },
    {
      href: "/career-prep/new-cases",
      icon: <AssignmentOutlined />,
      label: "New Cases",
    },
    {
      href: "/career-prep/showcase-eligible",
      icon: <TaskOutlined />,
      label: "Showcase Eligible",
    },
    {
      href: "/career-prep/placement-tracking",
      icon: <CalendarMonthOutlined />,
      label: "Application Status",
    },
    {
      href: "/career-prep/ict-recommendations",
      icon: <CalendarMonthOutlined />,
      label: "ICT Job Role Recommendations",
    },
    {
      href: "/career-prep/events",
      icon: <EditCalendarIcon />,
      label: "Events",
    },
    {
      href: "/career-prep/generic-job-match",
      icon: <UpdateOutlinedIcon />,
      label: "Generic job match",
    },
    {
      href: "/career-prep/add-company",
      icon: <PostAddOutlinedIcon />,
      label: "Create a company",
    },
    {
      href: "/career-prep/update-company",
      icon: <UpdateOutlinedIcon />,
      label: "Update a company",
    },
    {
      href: "/career-prep/postajob",
      icon: <PostAddOutlinedIcon />,
      label: "Post a job",
    },
    {
      href: "/career-prep/updatejob",
      icon: <UpdateOutlinedIcon />,
      label: "Update a job",
    },
  ];

  return (
    <>
      <Toolbar sx={{ height: "76px" }} />
      <div className="flex flex-col text-button-secondary-idle-text">
        <Stack
          direction={"row"}
          gap={1}
          sx={{ mt: "25px", alignItems: "center", ml: 5, mb: 3 }}
        >
          <Avatar scale={0.66} imgsrc={session?.user.image || ""} />
          <div>
            <p className="text-wrap font-bold">{session?.user.name}</p>
            <Link
              href={"/edit-profile/jobseeker/introduction"}
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
const DashboardHeader = ({
  handleDrawerToggle,
}: {
  handleDrawerToggle: () => void;
}) => (
  <AppBar
    position="sticky"
    variant="outlined"
    color="inherit"
    sx={{ zIndex: "10000", height: "76px", justifyContent: "center" }}
  >
    <Toolbar sx={{ justifyContent: "space-between", zIndex: "20000" }}>
      <Link href="/">
        <span className="sr-only">Tech Workforce Coalition</span>
        <Image
          src="/images/TWC_75x50_2024.svg"
          alt="Tech Workforce Coalition"
          width={75}
          height={50}
        />
      </Link>

      <Stack direction={"row"}>
        {/*<IconButton
                  color="inherit"
                  aria-label="open notifications"
                  edge="start"
                  sx={{ mr: { xs: 2, md: 4 } }}
                >
                  <NotificationsOutlined />
                </IconButton>*/}
        <AccountMenu />
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={handleDrawerToggle}
          sx={{ display: "block", ml: { xs: 2, md: 4 } }}
        >
          <Menu />
        </IconButton>
      </Stack>
    </Toolbar>
  </AppBar>
);
export default function layout({ children }: { children: React.ReactNode }) {
  const { data: session, status } = useSession();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleDrawerToggle = useCallback(() => {
    setMobileOpen(!mobileOpen);
  }, [mobileOpen]);

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

          {/* Main content with right drawer */}
          <div className="flex justify-between">
            {/* Main content area */}
            <div className="flex-1 p-4"></div>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <DashboardHeader handleDrawerToggle={handleDrawerToggle} />
      <Drawer
        variant="temporary"
        anchor="right"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          display: "block",
          "& .MuiDrawer-paper": {
            boxSizing: "border-box",
            width: drawerWidth,
          },
        }}
      >
        <CareerNavDrawer session={session} />
      </Drawer>
      <Box
        component="main"
        sx={{
          mt: "25px",
          flexGrow: 1,
          width: { md: `calc(100%)` },
        }}
      >
        {children}
      </Box>
    </div>
  );
}
