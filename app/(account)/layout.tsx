import "@/app/ui/global.css";

export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className={`flex min-h-screen flex-col laptop:h-screen`}>
      {children}
    </div>
  );
}
