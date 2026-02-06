export const metadata = {
  title: "Under Construction",
  description: "Sorry This page is currently under construction",
};
export default function page() {
  return (
    <div className="container h-[700px] mx-auto flex flex-col items-center justify-center space-y-8 px-8 py-16 md:px-12 lg:px-16">
      <h1 className="text-6xl">
        Sorry, this page is currently under construction
      </h1>
      <h2>
        Please{" "}
        <a
          className="underline"
          href="https://github.com/Computing-For-All/nextjs-issue-tracker/issues/new/choose"
        >
          file a bug
        </a>{" "}
        explaining how you got here and what you expected to find!
      </h2>
    </div>
  );
}
