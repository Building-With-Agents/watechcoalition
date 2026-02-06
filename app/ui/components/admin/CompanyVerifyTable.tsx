"use client";
import {
  Box,
  Button,
  Checkbox,
  Collapse,
  FormControlLabel,
  FormGroup,
  IconButton,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import KeyboardArrowDownIcon from "@mui/icons-material/KeyboardArrowDown";
import KeyboardArrowUpIcon from "@mui/icons-material/KeyboardArrowUp";
import { companies, employers, User } from "@prisma/client";
import React, { useState } from "react";
import CompanyDeleteButton from "./CompayDeleteButton";

function EmployeeRow({ employee }: { employee: employers & { users: User } }) {
  const [loadingEmployee, setLoadingEmployee] = useState(false);
  const [failedEmployee, setFailedEmployee] = useState(false); // eslint-disable-line @typescript-eslint/no-unused-vars
  const [verifedEmployee, setVerifedEmployee] = useState(
    employee.is_verified_employee,
  );
  const handleVerifyEmployee = async () => {
    try {
      setLoadingEmployee(true);
      const response = await fetch("/api/admin/verify/employer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          employerId: employee.employer_id,
          isVerified: !verifedEmployee,
        }),
      });

      if (response.ok) {
        const res = await response.json();
        setVerifedEmployee(res.is_verified_employee);
        setFailedEmployee(false);
      } else {
        setFailedEmployee(true);
        window.alert("Action Failed. Check your internet connection.");
      }
    } catch (error) {
      console.error("Error:", error);
      setFailedEmployee(true);
    } finally {
      setLoadingEmployee(false);
    }
  };
  return (
    <TableRow>
      <TableCell>
        {employee.users.first_name} {employee.users.last_name}
      </TableCell>
      <TableCell>{employee.users.email}</TableCell>
      <TableCell>
        <Button onClick={handleVerifyEmployee} disabled={loadingEmployee}>
          {loadingEmployee
            ? "Loading..."
            : verifedEmployee
              ? "Revoke Verification"
              : "Verify"}
        </Button>
      </TableCell>
    </TableRow>
  );
}

function Row({
  company,
}: {
  company: companies & { employers: (employers & { users: User })[] };
}) {
  const [open, setOpen] = React.useState(false);
  const [isApproved, setIsApproved] = useState(company.is_approved);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false); // eslint-disable-line @typescript-eslint/no-unused-vars
  const handleCompanyApprove = async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/admin/verify/company", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          companyId: company.company_id,
          isApproved: !isApproved,
        }),
      });
      if (response.ok) {
        await response.json();
        setIsApproved((prev) => !prev); // Update local state on success
      } else {
        window.alert("Action Failed Check your internet connection");
      }
    } catch (error) {
      console.error("Error:", error);
    } finally {
      setLoading(false);
    }
  };
  return (
    <React.Fragment>
      <TableRow sx={{ "& > *": { borderBottom: "unset" } }}>
        <TableCell>
          <IconButton
            aria-label={open ? "collapse row" : "expand row"}
            size="small"
            onClick={() => setOpen(!open)}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>
        <TableCell component="th" scope="row">
          {company.company_name}
        </TableCell>
        <TableCell>
          {isApproved ? "Approved" : "Not Approved"}
          <Button onClick={handleCompanyApprove} disabled={loading}>
            {loading ? "Loading.." : isApproved ? "Revoke Approval" : "Approve"}
          </Button>
        </TableCell>
        <TableCell>
          <CompanyDeleteButton companyId={company.company_id} />
        </TableCell>
      </TableRow>

      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6}>
          <Collapse in={open} timeout="auto">
            <Box sx={{ margin: 1 }}>
              <Typography variant="h6" gutterBottom component="div">
                Employees
              </Typography>
              <Table size="small" aria-label="applications">
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Email</TableCell>
                    <TableCell>Is Verified</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {company.employers.map((emp) => (
                    <EmployeeRow employee={emp} key={emp.employer_id} />
                  ))}
                </TableBody>
              </Table>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </React.Fragment>
  );
}
export default function CompanyVerifyTable(props: {
  companies: (companies & { employers: (employers & { users: User })[] })[];
}) {
  const [checked, setChecked] = React.useState(true);
  const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setChecked(event.target.checked);
  };
  const filteredCompanies = checked
    ? props.companies.filter(
        (company) =>
          !company.is_approved ||
          company.employers.some((e) => !e.is_verified_employee),
      )
    : props.companies;
  return (
    <Box sx={{ padding: 2 }}>
      <FormGroup>
        <FormControlLabel
          control={<Checkbox checked={checked} onChange={handleChange} />}
          label="Only Show Companies That Need Approval or have Unverfied Employees"
        />
      </FormGroup>
      <TableContainer component={Paper}>
        <Table aria-label="collapsible table">
          <TableHead>
            <TableRow>
              <TableCell />
              <TableCell>Company Name</TableCell>
              <TableCell>Is Approved</TableCell>
              <TableCell>Delete?</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCompanies.map((company) => (
              <Row company={company} key={company.company_id} />
            ))}
            {filteredCompanies.length == 0 && (
              <TableRow>
                <TableCell colSpan={6}>
                  No Companies are in need of approval at this time
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}
