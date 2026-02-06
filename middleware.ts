import { auth } from "@/auth-edge";
import { NextResponse } from "next/server";
import { Role } from "./data/dtos/UserInfoDTO";

export default auth((req) => {
  const pathname = req.nextUrl.pathname;
  const userRoles = req.auth?.user?.roles || [];
  const homeUrl = new URL("/", req.nextUrl.origin);

  // Map roles to their allowed routes
  const roleRoutes: Record<Role, string[]> = {
    [Role.GUEST]: [
      "/signup",
      "/signup/jobseeker",
      "/signup/employer",
      "/api/users/",
      "/api/users/role/update",
      "/api/users/avatar/upload",
      "/api/jobseekers/create",
      "/api/employers/create",
    ],
    [Role.JOBSEEKER]: [
      "/pdf.worker.min.mjs",
      "/edit-profile/jobseeker/",
      "/services/jobseekers/career-prep/skill-assessment",
      "/services/jobseekers/career-prep/enrollment",
      "/services/jobseekers/dashboard",
      "/services/jobseekers/dashboard/my-applications",
      "/services/jobseekers/",
      "/api/joblistings/",
      "/api/jobseekers/",
      "/api/edu-providers/",
      "/api/skills/search/",
      "/api/employers/technology-areas",
      "/api/users/avatar/upload",
      "/api/chatbot",
    ],
    [Role.EMPLOYER]: [
      "/pdf.worker.min.mjs",
      "/edit-profile/employer/",
      "/services/employers/dashboard",
      "/services/jobseekers/",
      "/api/jobseekers/get/",
      "/api/jobseekers/resume/get/",
      "/api/joblistings/",
      "/api/socc/",
      "/api/employers/",
      "/api/companies",
      "/api/users/avatar/upload",
      "/api/skills/search/",
      "/api/skills/parse-text/",
      "/api/postal-geo-data/zip/search",
      "/api/employer-feedback",
      "/api/ict/jobs-by-id",
      "/api/ict/recommendations",
    ],
    [Role.CASE_MANAGER]: [
      "/pdf.worker.min.mjs",
      "/api/admin",
      "/career-prep",
      "/services/jobseekers",
      "/api/admin/career-prep/self-assign-case",
      "/api/companies",
      "/api/jobseekers/career-prep/meeting",
      "/api/admin/career-prep/update-recomended-track/",
      "/api/joblistings/",
      "/api/skills/parse-text",
      "/api/ict/jobs-by-id",
      "/api/ict/recommendations",
      // Add any other routes accessible by case managers
    ],
    [Role.ADMIN]: [], // Admin has full access, so this can be empty
    [Role.EDUCATOR]: [], // Add routes for educators when needed
    [Role.VOLUNTEER]: [], // Add routes for volunteers when needed
  };

  const publicRoutes = [
    "/",
    "/about-us",
    "/ess",
    "/underconstruction",
    "/policies/terms-of-service",
    "/policies/privacy-policy",
    "/policies/user-data-agreement",
    "/signin",
    "/signout",
    "/services",
    "/services/events",
    "/services/events/registered",
    "/services/employers",
    "/services/employers/hiring-companies",
    "/services/employers/faq",
    "/services/jobseekers",
    "/services/joblistings",
    "/services/careers",
    "/services/careers/cybersecurity",
    "/services/careers/data-analytics",
    "/services/careers/it-cloud-support",
    "/services/careers/software-developer",
    "/services/training-providers",
    "/api/events/sign-up",
    "/api/events/registered",
    "/api/jobseekers/query",
    "/api/joblistings/query",
    "/api/employers/industry-sectors",
    "/api/postal-geo-data/city/get",
    "/api/postal-geo-data/city/search/",
    "/api/postal-geo-data/zip/search/",
    "/api/employers/training-providers",
    "/api/events",
    "/api/ogs",
    "/join",
    "/api/ai-workforce/contacts/submit",
  ];

  // Helper function to check if a path is allowed for any of the user's roles
  function userHasAccessToPath(path: string) {
    if (userRoles.includes(Role.ADMIN)) {
      // Admin has access to all routes
      // TODO: will have to restrict routes which rely on session data to display dynamic data based on employer and jobseeker id.
      console.log("Admin role recognized!");
      return true;
    }

    for (const role of userRoles) {
      const allowedRoutes = roleRoutes[role as Role] || [];
      if (allowedRoutes.some((route) => path.startsWith(route))) {
        return true;
      }
    }
    return false;
  }

  if (!req.auth && pathname === "/signout") {
    return NextResponse.redirect(homeUrl);
  }

  if (!req.auth) {
    const isProtectedRoute =
      !publicRoutes.includes(pathname) &&
      !pathname.startsWith("/ess") &&
      !pathname.startsWith("/services/joblistings") &&
      !pathname.startsWith("/services/training-programs") &&
      !pathname.startsWith("/api/postal-geo-data/city/search") &&
      !pathname.startsWith("/services/training-providers");

    if (isProtectedRoute) {
      const signInUrl = new URL("/signin", req.nextUrl.origin);
      signInUrl.searchParams.set(
        "callbackUrl",
        req.nextUrl.pathname + req.nextUrl.search,
      );
      return NextResponse.redirect(signInUrl);
    }
  }

  if (req.auth && userRoles.includes(Role.GUEST)) {
    if (
      roleRoutes.GUEST.includes(pathname) ||
      pathname == "/policies/terms-of-service" ||
      pathname == "/policies/privacy-policy" ||
      pathname == "/policies/user-data-agreement" ||
      pathname == "/signout"
    ) {
      return NextResponse.next();
    }
    return NextResponse.redirect(new URL("/signup", req.nextUrl.origin));
  }

  if (req.auth && pathname === "/signin") {
    if (userRoles.includes(Role.GUEST)) {
      return NextResponse.redirect(new URL("/signup", req.nextUrl.origin));
    }
    return NextResponse.redirect(homeUrl);
  }

  if (!req.auth && pathname.startsWith("/services/jobseekers/")) {
    return NextResponse.redirect(new URL("/signin", req.nextUrl.origin));
  }

  // Allow public routes
  if (
    publicRoutes.includes(pathname) || // training providers/programs needs wildcard for id, but all other public routes are explicit
    pathname.startsWith("/ess") ||
    pathname.startsWith("/services/training-programs/") ||
    pathname.startsWith("/services/training-providers/") ||
    pathname.startsWith("/api/postal-geo-data/city/search/") ||
    pathname.startsWith("/services/joblistings")
  ) {
    return NextResponse.next();
  }

  // Check if the user has access to the path based on their roles
  if (userHasAccessToPath(pathname)) {
    // Additional checks based on roles
    if (
      userRoles.includes(Role.JOBSEEKER) &&
      pathname.startsWith("/services/jobseekers/")
    ) {
      // REVIEW: Previously Jobseekers can only access their own profile, removed due to update in policy, however uncertain if any other conditionals effected
      // const requestedId = pathname.replace('/services/jobseekers/', '');
      // if (
      //   !pathname.startsWith('/services/jobseekers/dashboard') &&
      //   pathname !== '/services/jobseekers/career-prep/skill-assessment' &&
      //   pathname !== '/services/jobseekers/career-prep/enrollment' &&
      //   requestedId !== jobseekerId
      // ) {
      //   console.log(
      //     'Access denied: Jobseeker can only access their own profile',
      //   );
      //   return NextResponse.redirect(homeUrl);
      // }

      // Allow jobseekers to access any jobseeker profile
      return NextResponse.next();
    }

    // Case managers might have additional access controls
    // Implement any specific checks for CASE_MANAGER role if needed

    return NextResponse.next();
  }

  // If none of the roles grant access, redirect to the home page
  console.log(
    "Access denied: User does not have permission to access - " + pathname,
  );
  return NextResponse.redirect(homeUrl);
});

/* Match all request paths except for the ones starting with:
 * - api/auth (all auth routes are allowed)
 * - _next/static (static files)
 * - _next/image (image optimization files)
 * - images (...images. what did you expect?)
 * - favicon.ico, sitemap.xml, robots.txt (metadata files)
 */
export const config = {
  matcher: ["/((?!api/auth|_next/static|_next/image|images|favicon.ico).*)"],
};
