import { SignJWT, jwtVerify } from "jose";
import { cookies } from "next/headers";
import { NextResponse, NextRequest } from "next/server";

// !IMPORTANT this needs to be an env variable
const secretKey = "secret";
const key = new TextEncoder().encode(secretKey);
// a signed JWT is not encrypted, it's just proof that
// the content comes from us
// The purpose here is to make sure that the authorization granted
// like EMPLOYER or JOBSEEKER can pass around a jwt
// and not change their role
// It doesn't matter if a third party intercepts and sees this info
// NOTE: read up on if RS256 is better for us
export async function sign(payload: any) {
  return await new SignJWT(payload)
    .setProtectedHeader({ alg: "HS256" })
    .setIssuedAt()
    .setExpirationTime("10 sec from now")
    .sign(key);
}

// verify that the content comes from us
export async function verify(input: string): Promise<any> {
  const { payload } = await jwtVerify(input, key, {
    algorithms: ["HS256"],
  });
  return payload;
}

export async function login(formData: FormData) {
  const user = {
    email: formData.get("email"),
    password: formData.get("password"),
  };

  if (!user.email || !user.password) {
    return "Email and password are required.";
  }

  // create the session
  const expires = new Date(Date.now() + 10 * 1000);
  const session = await sign({ user, expires });

  // Save the session in a cookie
  (await cookies()).set("session", session, { expires, httpOnly: true });
}

export async function logout() {
  // Destroy the session
  (await cookies()).set("session", "", { expires: new Date(0) });
}

export async function getSession() {
  const session = (await cookies()).get("session")?.value;
  if (!session) return null;
  return await verify(session);
}

// TODO: Ask Keith if this is deprecated?
export async function updateSession(request: NextRequest) {
  const session = request.cookies.get("session")?.value;
  if (!session) return;

  // Refresh the session so it doesn't expire
  const parsed = await verify(session);
  parsed.expires = new Date(Date.now() + 10 * 1000);
  const res = NextResponse.next();
  res.cookies.set({
    name: "session",
    value: await sign(parsed),
    httpOnly: true,
    expires: parsed.expires,
  });
  return res;
}
