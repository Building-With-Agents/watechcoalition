import "@/app/ui/global.css";
import Footer from "@/app/ui/Footer";
import SignupHeader from "@/app/ui/SignupHeader";

export const metadata = {
  title: "Tech Workforce Coalition - Signin",
  description: "Tech Workforce Coalition Signin",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div>
      <SignupHeader />
      {children}
      <Footer />
    </div>
  );
}
