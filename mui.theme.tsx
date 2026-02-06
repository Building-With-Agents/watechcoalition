"use client";
import { createTheme } from "@mui/material/styles";

declare module "@mui/material/styles" {
  interface Palette {
    neutral: {
      white: string;
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
      700: string;
      800: string;
      900: string;
      black: string;
    };
    blue: {
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
      700: string;
    };
    green: {
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
      700: string;
      800: string;
    };
  }

  interface PaletteOptions {
    neutral?: {
      white: string;
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
      700: string;
      800: string;
      900: string;
      black: string;
    };
    blue?: {
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
      700: string;
    };
    green?: {
      100: string;
      200: string;
      300: string;
      400: string;
      500: string;
      600: string;
      700: string;
      800: string;
    };
  }
}

const theme = createTheme({
  cssVariables: true,
  colorSchemes: {
    light: {
      palette: {
        primary: {
          main: "#047F9C",
          light: "#C4EBF3",
        },
        secondary: {
          main: "#014260",
        },
        success: {
          main: "#61CE70",
        },
        warning: {
          main: "#EC7304",
        },
        error: {
          main: "#DB241C",
          light: "#F8D3D2",
        },
        neutral: {
          white: "#FFFFFF",
          100: "#F6F6F6",
          200: "#E5E5E5",
          300: "#CCCCCC",
          400: "#B3B3B3",
          500: "#999999",
          600: "#8F8F8F",
          700: "#707070",
          800: "#363636",
          900: "#191919",
          black: "#000000",
        },
        blue: {
          100: "#E1F5F9",
          200: "#D6F1F7",
          300: "#81BFCD",
          400: "#4FA5BA",
          500: "#3699B0",
          600: "#006682",
          700: "#003350",
        },
        green: {
          100: "#EFFAF1",
          200: "#DFF5E2",
          300: "#A0E2A9",
          500: "#2E9B3D",
          600: "#158124",
          400: "#81D88D",
          700: "#00680A",
          800: "#003500",
        },
      },
    },
    dark: false,
  },
  shape: {
    borderRadius: 8,
  },
  components: {},
});

export default theme;
