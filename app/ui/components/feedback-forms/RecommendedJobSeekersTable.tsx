"use client";

import { useEffect, useState } from "react";
import {
  TableContainer,
  Table,
  TableHead,
  TableRow,
  TableCell,
  TableBody,
  Link,
  Typography,
} from "@mui/material";

export default function RecommendedJobSeekersTable({
  jobRoleId,
}: {
  jobRoleId: string;
}) {
  const [jobseekers, setJobseekers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchJobseekers = async () => {
      const res = await fetch(`/api/ict/recommendations/${jobRoleId}`);
      const responseData = await res.json();
      setJobseekers(responseData || []);
      setLoading(false);
    };

    fetchJobseekers();
  }, [jobRoleId]);

  if (loading) return <Typography>Loading job seekers...</Typography>;

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Name</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {jobseekers.map((jobseeker) => (
            <TableRow key={jobseeker.jobseeker_id}>
              <TableCell>
                <Link href={"/services/jobseekers/" + jobseeker.jobseeker_id}>
                  {jobseeker.first_name} {jobseeker.last_name}
                </Link>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}
