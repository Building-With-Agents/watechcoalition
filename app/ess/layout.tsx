import { Box } from "@mui/material";
import Header from "@/app/ui/components/mui/Header";
import Footer from "../ui/Footer";

export default async function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Box>
      <Header />
      {children}
      <Footer />
    </Box>
  );
}
