// auth-edge.ts  (Edge-safe: no Prisma, no DB imports)
import NextAuth from "next-auth";
import GitHub from "next-auth/providers/github";
import Google from "next-auth/providers/google";
import MicrosoftEntraID from "next-auth/providers/microsoft-entra-id";

export const { auth } = NextAuth({
  // Keep it light: providers + jwt-only, no DB work here
  providers: [
    GitHub,
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
    }),
    MicrosoftEntraID({
      clientId: process.env.AUTH_MICROSOFT_ENTRA_ID_ID!,
      clientSecret: process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET!,
      issuer: `https://login.microsoftonline.com/${process.env.AUTH_MICROSOFT_ENTRA_ID_TENANT_ID}/v2.0`,
    }),
  ],
  session: { strategy: "jwt" }, // Edge-friendly
  callbacks: {
    async jwt({ token, trigger, session }) {
      // Allow client session updates to flow into the token
      if (trigger === "update" && session) Object.assign(token, session);
      // IMPORTANT: no DB lookups here
      return token;
    },
    async session({ session, token }) {
      // Surface token fields on session.user so middleware can read them
      session.user = { ...(session.user || {}), ...token } as any;
      return session;
    },
  },
  pages: { signIn: "/signin", newUser: "/signup" },
});
