import * as React from "react";
import Box from "@mui/material/Box";
import Avatar from "@mui/material/Avatar";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import ListItemIcon from "@mui/material/ListItemIcon";
import EditIcon from "@mui/icons-material/Edit";
import Divider from "@mui/material/Divider";
import Tooltip from "@mui/material/Tooltip";
import Logout from "@mui/icons-material/Logout";
import DashboardIcon from "@mui/icons-material/Dashboard";
import AccountBoxIcon from "@mui/icons-material/AccountBox";
import { useSession } from "next-auth/react";
import { ChevronDownIcon } from "@heroicons/react/20/solid";
import Button from "@mui/material/Button";
import { Role } from "@/data/dtos/UserInfoDTO";
import { usePathname } from "next/navigation";
import Link from "next/link";
import Login from "@mui/icons-material/Login";

export default function AccountMenu() {
  const { data: session } = useSession();
  const role = session?.user.roles;
  const pathname = usePathname();
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
    if (open) {
      handleClose();
    }
  };
  const handleClose = () => {
    setAnchorEl(null);
  };

  let textColor = "text-black";
  let borderColor = "border-black";
  if (
    pathname == "/services/jobseekers" ||
    pathname == "/services/employers" ||
    pathname == "/services/employers/hiring-companies" ||
    pathname.startsWith("/services/training-programs/")
  ) {
    textColor = "text-white";
    borderColor = "border-white";
  }
  if (!role) {
    return (
      <Link
        href={"/signin"}
        className={`px-6 py-2.5 rounded-[100px] ${textColor} border border-2 ${borderColor} hover:bg-gray-200`}
      >
        Sign In/Sign Up
      </Link>
    );
  }
  return (
    <React.Fragment>
      <Box sx={{ display: "flex", alignItems: "center", textAlign: "center" }}>
        <Tooltip title="Account settings">
          <Button
            onClick={handleClick}
            size="small"
            sx={{ ml: 2 }}
            aria-controls={open ? "account-menu" : undefined}
            aria-haspopup="true"
            aria-expanded={open ? "true" : undefined}
          >
            <p
              className={
                "flex hidden items-center text-sm normal-case sm-tablet:contents " +
                textColor
              }
            >
              {session?.user?.firstName || ""}
            </p>
            <ChevronDownIcon
              className={"h-5 w-5 flex-none " + textColor}
              aria-hidden="true"
            />
            <Avatar
              sx={{ width: 50, height: 50 }}
              alt={session?.user?.name || ""}
              src={session?.user?.image || ""}
            />
          </Button>
        </Tooltip>
      </Box>
      <Menu
        anchorEl={anchorEl}
        id="account-menu"
        open={open}
        onClose={handleClose}
        onClick={handleClose}
        slotProps={{
          paper: {
            elevation: 0,
            sx: {
              overflow: "visible",
              filter: "drop-shadow(0px 2px 8px rgba(0,0,0,0.32))",
              mt: 1.5,
              "& .MuiAvatar-root": {
                width: 32,
                height: 32,
                ml: -0.5,
                mr: 1,
              },
              "&::before": {
                content: '""',
                display: "block",
                position: "absolute",
                top: 0,
                right: 14,
                width: 10,
                height: 10,
                bgcolor: "background.paper",
                transform: "translateY(-50%) rotate(45deg)",
                zIndex: 0,
              },
            },
          },
        }}
        transformOrigin={{ horizontal: "right", vertical: "top" }}
        anchorOrigin={{ horizontal: "right", vertical: "bottom" }}
      >
        {role?.includes(Role.EMPLOYER) ? (
          <Link href="/services/employers/dashboard">
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <DashboardIcon fontSize="small" />
              </ListItemIcon>
              Dashboard
            </MenuItem>
          </Link>
        ) : (
          ""
        )}
        {role?.includes(Role.JOBSEEKER) ? (
          <Link href="/services/jobseekers/dashboard">
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <DashboardIcon fontSize="small" />
              </ListItemIcon>
              Dashboard
            </MenuItem>
          </Link>
        ) : (
          ""
        )}
        {role?.includes(Role.ADMIN) ? (
          <Link href="/admin">
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <DashboardIcon fontSize="small" />
              </ListItemIcon>
              Admin Dashboard
            </MenuItem>
          </Link>
        ) : (
          ""
        )}
        {role?.includes(Role.CASE_MANAGER) ? (
          <Link href="/career-prep">
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <DashboardIcon fontSize="small" />
              </ListItemIcon>
              Career Prep Dashboard
            </MenuItem>
          </Link>
        ) : (
          ""
        )}

        {role?.includes(Role.JOBSEEKER) ? (
          <Link href={"/services/jobseekers/" + session?.user.jobseekerId}>
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <AccountBoxIcon fontSize="small" />
              </ListItemIcon>
              My Profile
            </MenuItem>
          </Link>
        ) : (
          ""
        )}

        {role?.includes(Role.EMPLOYER) ? (
          <Link href="/edit-profile/employer/profile">
            <MenuItem onClick={handleClose}>
              <ListItemIcon>
                <EditIcon fontSize="small" />
              </ListItemIcon>
              Edit Profile
            </MenuItem>
          </Link>
        ) : (
          ""
        )}

        {role == undefined ? (
          <Link href={"/signin"}>
            <MenuItem>
              <ListItemIcon>
                <Login fontSize="small" />
              </ListItemIcon>
              Sign In
            </MenuItem>
          </Link>
        ) : (
          <div>
            <Divider />
            <Link href={"/signout"}>
              <MenuItem>
                <ListItemIcon>
                  <Logout fontSize="small" />
                </ListItemIcon>
                Logout
              </MenuItem>
            </Link>
          </div>
        )}
      </Menu>
    </React.Fragment>
  );
}
