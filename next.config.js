/** @type {import('next').NextConfig} */
const nextConfig = {
  env: {
    NEXTAUTH_URL: process.env.NEXTAUTH_URL,
  },
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "avatars.githubusercontent.com",
      },
      {
        protocol: "https",
        hostname: "careerservicesstorage.blob.core.windows.net",
      },
      {
        protocol: "https",
        hostname: "randomuser.me",
      },
      {
        protocol: "https",
        hostname: "logo.clearbit.com",
      },
      {
        protocol: "http",
        hostname: "example.com",
      },
      {
        protocol: "https",
        hostname: "example.test",
      },
      {
        protocol: "https",
        hostname: "i.pinimg.com",
      },
      {
        protocol: "https",
        hostname: "lh3.googleusercontent.com",
      },
      {
        protocol: "https",
        hostname: "encrypted-tbn0.gstatic.com",
      },
    ],
  },
};

export default nextConfig;
