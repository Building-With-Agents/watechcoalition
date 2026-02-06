import Image, { StaticImageData } from "next/image";
import Brooksource from "@/public/images/employers/BRK.svg";
import Accenture from "@/public/images/employers/Accenture.svg";
import GoldenSherpa from "@/public/images/employers/gs-logo-horizontal-white.svg";
import TekSystems from "@/public/images/employers/teksystems.svg";
import SeattleBank from "@/public/images/employers/Seattle-bank-logo.png";
import Provn from "@/public/images/employers/provn.png";
import { Box, Grid, Typography } from "@mui/material";

interface Logo {
  src: StaticImageData;
  alt: string;
  width: number;
}

const logos: Logo[] = [
  { src: GoldenSherpa, alt: "Golden Sherpa Logo", width: 290 },
  { src: TekSystems, alt: "TekSystems Logo", width: 152 },
  { src: Accenture, alt: "Accenture Logo", width: 152 },
  { src: SeattleBank, alt: "Seattle Bank Logo", width: 100 },
  { src: Brooksource, alt: "Brooksource Logo", width: 144 },
  { src: Provn, alt: "Provn Logo", width: 144 },
];

export default async function TrustedByEmployers() {
  return (
    <Box sx={{ my: 10, px: { xs: 2, sm: 3 } }}>
      <Typography
        variant="h4"
        color="textSecondary"
        sx={{ textAlign: "center", mb: 2 }}
      >
        Powering WA tech teams—from startups to Fortune 500s
      </Typography>
      <Grid
        container
        spacing={{ xs: 3, md: 3.75, lg: 7.5, xl: 12.5 }}
        sx={{
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        {logos.map((logo, index) => (
          <Grid
            container
            size={{ xs: 12, sm: 2 }}
            key={`row1-${index}`}
            sx={{
              justifyContent: "center",
            }}
          >
            <Image
              width={logo.width}
              src={logo.src}
              alt={logo.alt}
              quality={75}
            />
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
