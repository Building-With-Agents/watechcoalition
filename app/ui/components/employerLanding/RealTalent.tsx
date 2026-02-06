/* RealTalent.tsx */
import {
  Box,
  Grid,
  List,
  ListItem,
  ListItemText,
  Stack,
  Typography,
} from "@mui/material";
import Image from "next/image";

import alex_saudi from "./alex_saudi.jpg";
import jamie_chen from "./jamie_chen.jpg";
import ravi_patel from "./ravi_patel.jpg";
import morgan_lee from "./morgan_lee.jpg";
import { JSX } from "react";

const talentData = [
  {
    name: "Alex Saudi",
    image: alex_saudi,
    alt: "A person wearing a blue shirt, smiling",
    graduation: "Spring ‘26",
    program: "CFA Data Analytics",
    skills: "SQL, Tableau, Power BI, Python‑pandas",
    hiredBy: "Fortune 100",
  },
  {
    name: "Jamie Chen",
    image: jamie_chen,
    alt: "A person facing a camera, smiling",
    graduation: "Fall ‘25",
    program: "MBA in Marketing",
    skills: "Google Analytics, SEO, Content Strategy, Adobe Creative Suite",
    hiredBy: "Global Marketing Agency",
  },
  {
    name: "Ravi Patel",
    image: ravi_patel,
    alt: "A person facing a camera, smiling",
    graduation: "Winter ‘27",
    program: "MS in Cybersecurity",
    skills: "Python, Network Security, Ethical Hacking, Cloud Computing",
    hiredBy: "Leading Tech Firm",
  },
  {
    name: "Morgan Lee",
    image: morgan_lee,
    alt: "A person facing a camera",
    graduation: "Summer ‘24",
    program: "BA in Graphic Design",
    skills: "Sketch, Figma, Branding, User Experience Design",
    hiredBy: "Creative Studio",
  },
];

export default function RealTalent() {
  const cards: JSX.Element[] = [];

  for (const person of talentData) {
    cards.push(
      <Stack
        key={person.name}
        size={{ xs: 12, md: 3 }}
        component={Grid}
        spacing={2.5}
      >
        {/* Image */}
        <Box sx={{ position: "relative", width: "100%", pt: "100%" }}>
          <Image
            src={person.image}
            fill
            alt={person.alt}
            style={{ borderRadius: "25px", objectFit: "cover" }}
          />
        </Box>

        {/* Name */}
        <Typography variant="h4">{person.name}</Typography>

        {/* Details */}
        <List dense disablePadding>
          <ListItem disablePadding disableGutters>
            <ListItemText secondary={`Graduation: ${person.graduation}`} />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText secondary={`Program: ${person.program}`} />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText secondary={`Skill stack: ${person.skills}`} />
          </ListItem>
          <ListItem disableGutters>
            <ListItemText secondary={`Hired by: ${person.hiredBy}`} />
          </ListItem>
        </List>
      </Stack>,
    );
  }

  return (
    <Box sx={{ my: 10, px: { xs: 1, md: 5, lg: 10 } }}>
      <Typography
        variant="h1"
        color="secondary"
        sx={{ fontWeight: 500, pb: 10 }}
      >
        Real Numbers, Real Talent
      </Typography>

      <Grid container spacing={{ xs: 2.5, lg: 5 }}>
        {cards}
      </Grid>
    </Box>
  );
}
