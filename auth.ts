import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";
import MicrosoftEntraID from "next-auth/providers/microsoft-entra-id";
import type { Provider } from "next-auth/providers";
import { Role } from "./data/dtos/UserInfoDTO";
import { createUser, getUserByEmail } from "./app/lib/user";
import { devLog } from "@/app/lib/utils";

const providers: Provider[] = [
  GitHub,
  Google({
    clientId: process.env.GOOGLE_CLIENT_ID,
    clientSecret: process.env.GOOGLE_CLIENT_SECRET,
  }),
  MicrosoftEntraID({
    clientId: process.env.AUTH_MICROSOFT_ENTRA_ID_ID,
    clientSecret: process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET,
    issuer: `https://login.microsoftonline.com/${process.env.AUTH_MICROSOFT_ENTRA_ID_TENANT_ID}/v2.0`,
  }),
];

export const providerMap = providers.map((provider) => {
  if (typeof provider === "function") {
    const providerData = provider();
    return { id: providerData.id, name: providerData.name };
  } else {
    return { id: provider.id, name: provider.name };
  }
});

export const { handlers, auth, signIn, signOut } = NextAuth({
  debug: true,
  providers,
  callbacks: {
    async jwt({ token, user, trigger, session }) {
      try {
        if (trigger === "update") {
          // Iterate over the session properties and dynamically update the token
          Object.entries(session).forEach(([key, value]) => {
            // Dynamically assign updated properties to the token
            if (value !== undefined) {
              token[key] = value;
            }
          });
        }
        if (user && user.email) {
          let fetchResponse;
          let createResponse;

          try {
            fetchResponse = await getUserByEmail(user.email);

            if (!fetchResponse) {
              //user doesn't exist in database
              const userData = {
                email: user.email,
                firstName: user.name?.split(" ")[0] || "",
                lastName: user.name?.split(" ")[1] || "",
                image: user.image,
                roles: [Role.GUEST], // default role
              };
              devLog("server-side-default-role\n", userData);

              // add user to database
              createResponse = await createUser(userData);

              if (!createResponse) {
                console.error("Failed to create user");
                throw new Error("Failed to create user");
              }

              devLog("User created successfully:", createResponse);

              //assign database values to the token after user is created
              token.id = createResponse.userId;
              token.email = createResponse.email;
              token.firstName = createResponse.firstName;
              token.lastName = createResponse.lastName;
              token.roles = createResponse.roles;
              token.jobseekerId = createResponse.jobseekerId || null;
              token.employerId = createResponse.employerId;
              token.companyId = createResponse.companyId;
              token.companyIsApproved = createResponse.companyIsApproved;
              token.employeeIsApproved = createResponse.employeeIsApproved;
              token.image = createResponse.image
                ? createResponse.image
                : (user.image ?? undefined);
            } else {
              // user already exists in database assign the database values to the token
              token.id = fetchResponse.userId;
              token.firstName = fetchResponse.firstName;
              token.lastName = fetchResponse.lastName;
              token.roles = fetchResponse.roles;
              token.email = fetchResponse.email;
              token.jobseekerId = fetchResponse.jobseekerId;
              token.employerId = fetchResponse.employerId;
              token.companyId = fetchResponse.companyId;
              token.companyIsApproved = fetchResponse.companyIsApproved;
              token.employeeIsApproved = fetchResponse.employeeIsApproved;
              token.image = fetchResponse.image
                ? fetchResponse.image
                : (user.image ?? undefined);
            }
          } catch (error) {
            console.error("Error during user fetch/create:", error);
            throw new Error("Failed to handle user authentication");
          }
        }
      } catch (error) {
        console.error("Error in JWT callback:", error);
        throw new Error("Failed to handle user authentication");
      }

      return token;
    },
    async session({ session, token }) {
      session.user.jobseekerId = token.jobseekerId;
      session.user.employerId = token.employerId;
      session.user.companyId = token.companyId;
      session.user.companyIsApproved = token.companyIsApproved;
      session.user.employeeIsApproved = token.employeeIsApproved;
      session.user.id = token.id;
      session.user.firstName = token.firstName;
      session.user.lastName = token.lastName;
      session.user.email = token.email;
      session.user.roles = token.roles;
      session.user.image = token.image;
      return session;
    },
    async redirect({ url, baseUrl }) {
      if (url.startsWith("/")) {
        return `${baseUrl}${url}`;
      }
      if (new URL(url).origin === baseUrl) {
        return url;
      }
      return baseUrl;
    },
  },
  pages: {
    signIn: "/signin",
    newUser: "/signup",
  },
  cookies: {
    pkceCodeVerifier: {
      name: "next-auth.pkce.code_verifier",
      options: {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        secure: true,
        domain: process.env.NEXT_PUBLIC_DOMAIN || "localhost",
      },
    },
  },
});
