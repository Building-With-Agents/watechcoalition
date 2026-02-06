"use client";

import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useSession } from "next-auth/react";
import {
  AppBar,
  Toolbar,
  IconButton,
  Button,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Menu,
  MenuItem,
  Box,
} from "@mui/material";
import {
  Menu as MenuIcon,
  ArrowDropDown as ArrowDropDownIcon,
  Close as CloseIcon,
  ExpandMore as ExpandMoreIcon,
} from "@mui/icons-material";

import AccountMenu from "@/app/ui/components/mui/AccountMenu";
import {
  BuildingOffice2Icon,
  BriefcaseIcon,
  NewspaperIcon,
  QuestionMarkCircleIcon,
} from "@heroicons/react/24/outline";
import GreenMarketingBanner from "../GreenMarketingBanner";

type TopLevelLink = {
  name: string;
  dropDowns?: {
    name: string;
    href: string;
    target?: string;
    rel?: string;
    icon?: React.ElementType;
  }[];
  href?: string;
};

const TopLevelLinks: TopLevelLink[] = [
  {
    name: "For Employers",
    dropDowns: [
      {
        name: "See the value",
        href: "/services/employers",
        icon: BuildingOffice2Icon,
      },
    ],
  },
  {
    name: "For Jobseekers",
    dropDowns: [
      {
        name: "Learn More & Join",
        href: "/services/jobseekers",
        icon: BriefcaseIcon,
      },
      {
        name: "Job Listings",
        href: "/services/joblistings",
        icon: NewspaperIcon,
      },
      {
        name: "Career Paths",
        href: "/services/careers",
        icon: QuestionMarkCircleIcon,
      },
    ],
  },
  // {
  //   name: "Our Community",
  //   dropDowns: [
  //     {
  //       name: "Join Our Community",
  //       href: "https://forum.watechwfcoalition.org/",
  //       target: "_blank",
  //       rel: "noopener noreferrer",
  //       icon: UsersIcon,
  //     },
  //     {
  //       name: "Careers",
  //       href: "/services/careers", //TODO: Need to update Logos and training offerings before making this live
  //       icon: QuestionMarkCircleIcon,
  //     },
  //   ],
  // },
  // {
  //   name: "Partners",
  //   dropDowns: [
  //     {
  //       name: "Training Providers",
  //       href: "/services/training-providers",
  //       icon: UserGroupIcon,
  //     },
  //   ],
  // },
  // { name: "Events", href: "/services/events" },
  { name: "About Us", href: "/about-us" },
] as const;

export default function Header() {
  const pathname = usePathname();
  const session = useSession();
  const loggedin = session.status === "authenticated";
  const [mobileOpen, setMobileOpen] = useState(false);
  const toggleDrawer = (open: boolean) => () => {
    setMobileOpen(open);
  };

  const [expanded, setExpanded] = useState<string | false>(false);

  const handleAccordionToggle =
    (panel: string) => (event: React.SyntheticEvent, isExpanded: boolean) => {
      setExpanded(isExpanded ? panel : false);
    };

  const [anchorEl, setAnchorEl] = useState<{
    [key: string]: HTMLElement | null;
  }>({});
  const handleMenuOpen = (
    event: React.MouseEvent<HTMLButtonElement>,
    name: string,
  ) => {
    setAnchorEl((prev) => ({ ...prev, [name]: event.currentTarget }));
  };
  const handleMenuClose = (name: string) => {
    setAnchorEl((prev) => ({ ...prev, [name]: null }));
  };

  const isTransparent =
    [
      "/services/jobseekers",
      "/services/employers",
      "/services/employers/hiring-companies",
      "/services/careers",
    ].includes(pathname) || pathname.startsWith("/services/training-programs/");

  const appBarStyles = {
    position: isTransparent ? "absolute" : "static",
    backgroundColor: isTransparent ? "transparent" : "inherit",
    boxShadow: "none",
    border: "none",
    width: "100%",
    color: isTransparent ? "neutral.white" : "inherit",
    padding: 2,
    top: 0,
  };
  if (!loggedin) {
    appBarStyles.top = isTransparent ? 60 : 30;
  }

  return (
    <>
      <GreenMarketingBanner show={!loggedin} />
      <AppBar sx={appBarStyles}>
        <Toolbar disableGutters>
          {isTransparent ? (
            <Link href="/">
              <span className="sr-only">Tech Workforce Coalition</span>
              <Image
                src="/images/TWC logo_White.svg"
                alt="Tech Workforce Coalition"
                width={75}
                height={31.8}
              />
            </Link>
          ) : (
            <Link href="/">
              <span className="sr-only">Tech Workforce Coalition</span>
              <Image
                src="/images/TWC_75x50_2024.svg"
                alt="Tech Workforce Coalition"
                width={75}
                height={31.8}
              />
            </Link>
          )}

          <Box
            sx={{
              display: { xs: "none", md: "flex" },
              flexGrow: 1,
              alignItems: "center",
              justifyContent: "center",
              gap: 3,
            }}
          >
            {TopLevelLinks.map((link) =>
              link.dropDowns ? (
                <Box key={link.name}>
                  <Button
                    onClick={(e) => handleMenuOpen(e, link.name)}
                    endIcon={<ArrowDropDownIcon />}
                    sx={{ color: "inherit", textTransform: "none" }}
                  >
                    {link.name}
                  </Button>
                  <Menu
                    anchorEl={anchorEl[link.name]}
                    open={Boolean(anchorEl[link.name])}
                    onClose={() => handleMenuClose(link.name)}
                    disableScrollLock
                  >
                    {link.dropDowns.map((item) => (
                      <MenuItem
                        sx={{ px: 3, py: 2 }}
                        key={item.name}
                        component={Link}
                        href={item.href}
                        target={item.target || "_self"}
                        rel={item.rel || ""}
                        onClick={() => handleMenuClose(link.name)}
                      >
                        {item.icon && (
                          <Box
                            component={item.icon}
                            sx={{ width: 20, height: 20, marginRight: 1 }}
                          />
                        )}
                        {item.name}
                      </MenuItem>
                    ))}
                  </Menu>
                </Box>
              ) : (
                <Button
                  key={link.name}
                  component={Link}
                  href={link.href!}
                  sx={{
                    color: "inherit",
                    textTransform: "none",
                  }}
                >
                  {link.name}
                </Button>
              ),
            )}
          </Box>

          <Box sx={{ marginLeft: "auto" }}>
            <AccountMenu />
          </Box>
          <IconButton
            color="inherit"
            aria-label="Open main menu"
            onClick={toggleDrawer(true)}
            sx={{ display: { md: "none" }, marginLeft: 1 }}
          >
            <MenuIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <Drawer
        anchor="right"
        open={mobileOpen}
        onClose={toggleDrawer(false)}
        slotProps={{
          paper: { sx: { width: 250, p: 2 } },
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            mb: 2,
          }}
        >
          <IconButton
            onClick={toggleDrawer(false)}
            sx={{ display: "flex", justifyContent: "flex-end" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>

        <List>
          {TopLevelLinks.map((link) =>
            link.dropDowns ? (
              <Accordion
                key={link.name}
                expanded={expanded === link.name}
                onChange={handleAccordionToggle(link.name)}
                disableGutters
                sx={{
                  boxShadow: "none",
                  backgroundColor: "transparent",
                  "&:before": { display: "none" },
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon />}
                  sx={{ px: 2 }}
                >
                  <ListItemText
                    primary={link.name}
                    sx={{ fontWeight: "bold" }}
                  />
                </AccordionSummary>
                <AccordionDetails sx={{ p: 0 }}>
                  {link.dropDowns.map((item) => (
                    <ListItemButton
                      key={item.name}
                      component={Link}
                      href={item.href}
                      target={item.target || "_self"}
                      rel={item.rel || ""}
                      onClick={toggleDrawer(false)}
                      sx={{ pl: 4 }}
                    >
                      <ListItemText primary={item.name} />
                    </ListItemButton>
                  ))}
                </AccordionDetails>
              </Accordion>
            ) : (
              <ListItemButton
                key={link.name}
                component={Link}
                href={link.href!}
                onClick={toggleDrawer(false)}
              >
                <ListItemText primary={link.name} />
              </ListItemButton>
            ),
          )}
        </List>
      </Drawer>
    </>
  );
}
