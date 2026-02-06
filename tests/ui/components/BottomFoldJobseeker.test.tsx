import { render, screen, cleanup, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import BottomFoldJobseeker from "../../../app/ui/components/BottomFoldJobseeker";
import { SessionProvider } from "next-auth/react";

vi.mock("next/server", () => ({}));
vi.mock("next-auth/react", () => ({
  useSession: vi.fn(() => ({
    expires: "1",
    user: {
      email: "bagel@bagel.com",
      name: "Bagel",
      image: "/images/loveBagels.jpg",
    },
  })),
  SessionProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

const renderWithProviders = (ui: React.ReactElement) => {
  return render(<SessionProvider>{ui}</SessionProvider>);
};

describe("BottomFoldJobSeeker", () => {
  afterEach(() => {
    cleanup();
    vi.resetAllMocks();
  });

  it("renders the div text", async () => {
    vi.mock("@/auth", () => ({
      auth: vi.fn(() => Promise.resolve(null)),
    }));
    renderWithProviders(await BottomFoldJobseeker());
    await waitFor(() => {
      expect(
        screen.getByText("Stand Out and Unlock New Opportunities"),
      ).toBeDefined();
    });
  });

  it("renders the sign up button", async () => {
    vi.mock("@/auth", () => ({
      auth: vi.fn(() => Promise.resolve(null)),
    }));
    renderWithProviders(await BottomFoldJobseeker());
    await waitFor(() => {
      expect(screen.getByText("Create Profile")).toBeDefined();
    });
  });
});
