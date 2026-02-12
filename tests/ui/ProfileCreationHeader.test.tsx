import { render, screen, cleanup } from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import { SessionProvider, useSession } from "next-auth/react";
import ProfileCreationHeader from "../../app/ui/ProfileCreationHeader";
import { Role } from "@/data/dtos/UserInfoDTO";
import { Session } from "next-auth";

vi.mock("next-auth/react", () => ({
  useSession: vi.fn(),
  SessionProvider: ({ children }: { children: React.ReactNode }) => (
    <div>{children}</div>
  ),
}));

const renderWithProviders = (ui: React.ReactElement, role: Role) => {
  vi.mocked(useSession).mockImplementation(() => ({
    update: async (): Promise<Session | null> => null, // Update the return type of the update function
    data: {
      expires: "1",
      user: {
        id: "test-user-id",
        email: "bagel@bagel.com",
        name: "Bagel",
        image: "/images/loveBagels.jpg",
        roles: [role],
        firstName: "bagel",
        lastName: "test",
        createdAt: new Date(),
        updatedAt: new Date(),
        companyIsApproved: false,
        employeeIsApproved: false,
      },
    },
    status: "authenticated",
  }));
  return render(<SessionProvider>{ui}</SessionProvider>);
};

describe("ProfileCreationHeader", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders correctly", () => {
    renderWithProviders(<ProfileCreationHeader />, Role.JOBSEEKER);
    expect(screen.getByRole("banner")).toBeDefined();
    expect(screen.getByAltText("Tech Workforce Coalition")).toBeDefined();
    // expect(screen.getByText('Skip')).toBeDefined();
  });

  // it('links to the correct dashboard for employers', () => {
  //     renderWithProviders(<ProfileCreationHeader />, Role.EMPLOYER);
  //     expect(screen.getByText('Skip').closest('a')).toHaveProperty('pathname', '/services/employers/dashboard');
  // });

  // it('links to the correct dashboard for jobseekers', () => {
  //     renderWithProviders(<ProfileCreationHeader />, Role.JOBSEEKER);
  //     expect(screen.getByText('Skip').closest('a')).toHaveProperty('pathname', '/services/jobseekers/dashboard');
  // });
});
