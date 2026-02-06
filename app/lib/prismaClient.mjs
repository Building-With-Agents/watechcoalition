import { PrismaClient } from "@prisma/client";

let prisma;

const getPrismaClient = () => {
  // Ensure we're only using the global object in server environments
  if (typeof window === "undefined") {
    // Check if we're in production or development mode
    if (process.env.NODE_ENV === "production") {
      if (!prisma) {
        prisma = new PrismaClient();
      }
    } else {
      // In development, attach to the globalThis object to prevent re-creation during hot reloads
      if (!globalThis.prisma) {
        globalThis.prisma = new PrismaClient();
      }
      prisma = globalThis.prisma;
    }
  }

  return prisma;
};

export default getPrismaClient;
