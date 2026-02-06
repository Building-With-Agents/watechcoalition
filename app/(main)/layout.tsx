import Header from "@/app/ui/components/mui/Header";
import Footer from "@/app/ui/Footer";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex h-screen flex-col">
      <Header />
      <div className="grow">{children}</div>
      <Footer />
    </div>
  );
}
