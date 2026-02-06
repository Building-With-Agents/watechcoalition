"use client";
import React, { useState, useEffect, useCallback } from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  CircularProgress,
  Box,
  Link,
  Button,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import DownloadIcon from "@mui/icons-material/Download";
import { ICTRecommendationResult } from "@/app/lib/ict";

type ApiRoleInfo = {
  role_id: string;
  title: string;
};

type ApiPathwayStructure = {
  pathway_id: string;
  pathway_title: string;
  roles: ApiRoleInfo[];
};

type Seeker = {
  user_id: string;
  jobseeker_id: string;
  hasResume: boolean;
  first_name: string;
  last_name: string;
  email: string;
  final_score: number;
};

interface RoleGroup {
  roleId: string;
  roleTitle: string;
  seekers: Seeker[];
  isLoadingSeekers: boolean;
  hasFetchedSeekers: boolean;
  errorSeekers?: string | null;
}

interface PathwayGroup {
  pathwayId: string;
  pathwayTitle: string;
  roles: RoleGroup[];
}

interface SeekerRowProps {
  seeker: Seeker;
  roleId: string;
  isLoadingResume: boolean;
  onFetchResume: (userId: string) => void;
}

const SeekerRow = React.memo(
  function SeekerRowComponent({
    seeker,
    roleId,
    isLoadingResume,
    onFetchResume,
  }: SeekerRowProps) {
    return (
      <TableRow key={`${roleId}-${seeker.jobseeker_id}`} hover>
        <TableCell>
          <Link
            target="_blank"
            href={`/services/jobseekers/${seeker.jobseeker_id}`}
          >
            {seeker.first_name} {seeker.last_name}
          </Link>
        </TableCell>
        <TableCell>
          <Link target="_blank" href={`mailto:${seeker.email}`}>
            {seeker.email}
          </Link>
        </TableCell>
        <TableCell>
          {seeker.hasResume && (
            <Button
              size="small"
              startIcon={<DownloadIcon fontSize="small" />}
              onClick={() => onFetchResume(seeker.user_id)}
              disabled={isLoadingResume}
            >
              {isLoadingResume ? "Loading…" : "Fetch Resume"}
            </Button>
          )}
        </TableCell>
        <TableCell align="right">{seeker.final_score.toFixed(3)}</TableCell>
      </TableRow>
    );
  },
  (prev, next) =>
    prev.seeker.jobseeker_id === next.seeker.jobseeker_id &&
    prev.isLoadingResume === next.isLoadingResume &&
    prev.seeker.final_score === next.seeker.final_score,
);

export default function ICTRecommendationTable() {
  const [pathwayData, setPathwayData] = useState<PathwayGroup[]>([]);
  const [initialLoading, setInitialLoading] = useState(true);
  const [initialError, setInitialError] = useState<string | null>(null);
  const [resumeLoadingId, setResumeLoadingId] = useState<string | null>(null);

  useEffect(() => {
    setInitialLoading(true);
    fetch("/api/admin/career-prep/jobroles-by-pathway")
      .then(async (res) => {
        if (!res.ok) {
          const err = await res.json();
          throw new Error(err.error || `HTTP ${res.status}`);
        }
        return res.json() as Promise<ApiPathwayStructure[]>;
      })
      .then((apiPathways) => {
        const transformedData: PathwayGroup[] = apiPathways
          .filter((p) => p.roles.length > 0)
          .map((p) => ({
            pathwayId: p.pathway_id,
            pathwayTitle: p.pathway_title,
            roles: p.roles.map((r) => ({
              roleId: r.role_id,
              roleTitle: r.title,
              seekers: [],
              isLoadingSeekers: false,
              hasFetchedSeekers: false,
              errorSeekers: null,
            })),
          }));
        setPathwayData(transformedData);
      })
      .catch((err: Error) => {
        console.error("Error fetching pathway structure:", err);
        setInitialError(err.message);
      })
      .finally(() => setInitialLoading(false));
  }, []);

  const handleFetchSeekersForRole = useCallback(
    async (pathwayIndex: number, roleIndex: number) => {
      const role = pathwayData[pathwayIndex]?.roles[roleIndex];
      if (!role || role.isLoadingSeekers || role.hasFetchedSeekers) {
        return;
      }

      setPathwayData((prevData) => {
        const newData = [...prevData];
        const pathwayToUpdate = { ...newData[pathwayIndex] };
        const roleToUpdate = { ...pathwayToUpdate.roles[roleIndex] };
        roleToUpdate.isLoadingSeekers = true;
        roleToUpdate.errorSeekers = null;
        pathwayToUpdate.roles = [...pathwayToUpdate.roles];
        pathwayToUpdate.roles[roleIndex] = roleToUpdate;
        newData[pathwayIndex] = pathwayToUpdate;
        return newData;
      });

      try {
        const res = await fetch(`/api/ict/recommendations/${role.roleId}`);
        const responseData = await res.json();

        if (!res.ok) {
          throw new Error(responseData.error || `HTTP ${res.status}`);
        }

        let seekersResults: ICTRecommendationResult[] = [];
        if (
          responseData.message &&
          Array.isArray(responseData.results) &&
          responseData.results.length === 0
        ) {
          seekersResults = [];
        } else if (Array.isArray(responseData)) {
          seekersResults = responseData as ICTRecommendationResult[];
        } else if (responseData.message) {
          seekersResults = [];
        }

        seekersResults.sort((a, b) => b.final_score - a.final_score);

        const mappedSeekers: Seeker[] = seekersResults.map((s) => ({
          user_id: s.id,
          jobseeker_id: s.jobseeker_id,
          hasResume: s.hasResume,
          first_name: s.first_name,
          last_name: s.last_name,
          email: s.email,
          final_score: s.final_score,
        }));

        setPathwayData((prevData) => {
          const newData = [...prevData];
          const pathwayToUpdate = { ...newData[pathwayIndex] };
          const roleToUpdate = { ...pathwayToUpdate.roles[roleIndex] };
          roleToUpdate.seekers = mappedSeekers;
          roleToUpdate.isLoadingSeekers = false;
          roleToUpdate.hasFetchedSeekers = true;
          pathwayToUpdate.roles = [...pathwayToUpdate.roles];
          pathwayToUpdate.roles[roleIndex] = roleToUpdate;
          newData[pathwayIndex] = pathwayToUpdate;
          return newData;
        });
      } catch (e: any) {
        console.error(`Failed to fetch seekers for role ${role.roleId}:`, e);
        setPathwayData((prevData) => {
          const newData = [...prevData];
          const pathwayToUpdate = { ...newData[pathwayIndex] };
          const roleToUpdate = { ...pathwayToUpdate.roles[roleIndex] };
          roleToUpdate.isLoadingSeekers = false;
          roleToUpdate.hasFetchedSeekers = true;
          roleToUpdate.errorSeekers =
            e.message || "Failed to load recommendations";
          pathwayToUpdate.roles = [...pathwayToUpdate.roles];
          pathwayToUpdate.roles[roleIndex] = roleToUpdate;
          newData[pathwayIndex] = pathwayToUpdate;
          return newData;
        });
      }
    },
    [pathwayData],
  );

  const handleFetchResume = useCallback(async (userId: string) => {
    setResumeLoadingId(userId);
    try {
      const res = await fetch(`/api/jobseekers/resume/get/${userId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status} ${await res.text()}`);
      const url = await res.json();
      window.open(url, "_blank");
    } catch (e: any) {
      console.error("Failed to fetch resume:", e.message);
      alert("Could not fetch resume.");
    } finally {
      setResumeLoadingId(null);
    }
  }, []);

  if (initialLoading) {
    return (
      <Box display="flex" justifyContent="center" p={4}>
        <CircularProgress />
      </Box>
    );
  }
  if (initialError) {
    return (
      <Box p={4}>
        <Typography color="error" align="center">
          Error loading pathway data: {initialError}
        </Typography>
      </Box>
    );
  }
  if (pathwayData.length === 0) {
    return (
      <Box p={4}>
        <Typography align="center">No pathways found.</Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ width: "100%" }}>
      {pathwayData.map((pg, pathwayIndex) => (
        <Accordion key={pg.pathwayId} sx={{ bgcolor: "neutral.100" }}>
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            <Typography variant="h5">{pg.pathwayTitle}</Typography>
          </AccordionSummary>
          <AccordionDetails>
            {pg.roles.map((role, roleIndex) => (
              <Accordion
                key={role.roleId}
                disableGutters
                onChange={(_event, expanded) => {
                  if (expanded) {
                    handleFetchSeekersForRole(pathwayIndex, roleIndex);
                  }
                }}
              >
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="h6">{role.roleTitle}</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  {role.isLoadingSeekers ? (
                    <Box display="flex" justifyContent="center" p={2}>
                      <CircularProgress size={24} />
                      <Typography sx={{ ml: 1 }}>
                        Loading recommendations...
                      </Typography>
                    </Box>
                  ) : role.errorSeekers ? (
                    <Typography color="error" sx={{ p: 2 }}>
                      Error: {role.errorSeekers}
                    </Typography>
                  ) : !role.hasFetchedSeekers ? (
                    <Typography sx={{ fontStyle: "italic", p: 2 }}>
                      Expand to load recommendations.
                    </Typography>
                  ) : role.seekers.length > 0 ? (
                    <TableContainer
                      component={Paper}
                      variant="outlined"
                      sx={{ mt: 1 }}
                    >
                      <Table size="small" stickyHeader>
                        <TableHead>
                          <TableRow>
                            <TableCell>Name</TableCell>
                            <TableCell>Email</TableCell>
                            <TableCell>Resume</TableCell>
                            <TableCell align="right">Match Score</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {role.seekers.map((s) => (
                            <SeekerRow
                              key={s.user_id}
                              seeker={s}
                              roleId={role.roleId}
                              isLoadingResume={resumeLoadingId === s.user_id}
                              onFetchResume={handleFetchResume}
                            />
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Typography sx={{ fontStyle: "italic", p: 2 }}>
                      No matching seekers found for this role.
                    </Typography>
                  )}
                </AccordionDetails>
              </Accordion>
            ))}
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
}
