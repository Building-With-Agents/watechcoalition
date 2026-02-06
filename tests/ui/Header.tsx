import {
  render,
  screen,
  fireEvent,
  cleanup,
  within,
} from "@testing-library/react";
import { describe, it, expect, vi, afterEach } from "vitest";
import Header from "../../app/ui/components/mui/Header";
import { usePathname } from "next/navigation";
import { SessionProvider } from "next-auth/react";

// Mock ResizeObserver
global.ResizeObserver = class {
  observe() {}
  unobserve() {}
  disconnect() {}
};

vi.mock("next/link", () => ({
  default: ({ children, ...props }: { children: React.ReactNode }) => (
    <a {...props}>{children}</a>
  ),
}));
vi.mock("next/image", () => ({
  default: (props: any) => <img {...props} />,
}));
vi.mock("next/navigation", () => ({
  usePathname: vi.fn(),
}));

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

vi.mock("./components/mui/AccountMenu", () => ({
  default: () => <div data-testid="account-menu">Account Menu</div>,
}));

const renderWithProviders = (ui: React.ReactElement) => {
  return render(<SessionProvider>{ui}</SessionProvider>);
};

describe("Header", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the logo and navigation links", async () => {
    vi.mocked(usePathname).mockReturnValue("/");
    renderWithProviders(<Header />);

    expect(screen.getByAltText("Tech Workforce Coalition")).toBeDefined();

    const topLinkForJobseekers = screen.getByText("For Jobseekers");
    expect(topLinkForJobseekers).toBeDefined();
    fireEvent.click(topLinkForJobseekers);
    // expect(screen.getByText('Landing Page')).not.toBeNull(); // Causes duplicate existence error
    expect(screen.getByText("Job Listings")).toBeDefined();

    const topLinkOurCommunity = screen.getByText("Our Community");
    expect(topLinkOurCommunity).toBeDefined();
    fireEvent.click(topLinkOurCommunity);
    expect(screen.getByText("Join Our Community")).toBeDefined();
    expect(screen.getByText("Careers")).toBeDefined();

    // expect(screen.getByText('Events')).toBeDefined();

    const topLinkPartners = screen.getByText("Partners");
    expect(topLinkPartners).toBeDefined();
    fireEvent.click(topLinkPartners);
    expect(screen.getByText("Training Providers")).toBeDefined();

    expect(screen.getByText("About Us")).toBeDefined();
  });

  it("changes logo based on pathname", () => {
    vi.mocked(usePathname).mockReturnValue("/services/jobseekers");
    renderWithProviders(<Header />);

    const logo = screen.getByAltText(
      "Tech Workforce Coalition",
    ) as HTMLImageElement;
    expect(logo.src).toContain("/images/TWC%20logo_White.svg");
  });

  it("renders correct links in mobile menu", () => {
    vi.mocked(usePathname).mockReturnValue("/");
    renderWithProviders(<Header />);

    fireEvent.click(screen.getByRole("button", { name: "Open main menu" }));

    const mobileMenu = screen.getByRole("presentation");

    const topLinkForJobseekers = within(mobileMenu).getByText("For Jobseekers");
    expect(topLinkForJobseekers).toBeDefined();
    fireEvent.click(topLinkForJobseekers);
    // expect(within(mobileMenu).getByText('Landing Page')).not.toBeNull(); // Causes duplicate existence error
    expect(within(mobileMenu).getByText("Job Listings")).toBeDefined();

    const topLinkOurCommunity = within(mobileMenu).getByText("Our Community");
    expect(topLinkOurCommunity).toBeDefined();
    fireEvent.click(topLinkOurCommunity);
    expect(within(mobileMenu).getByText("Join Our Community")).toBeDefined();
    expect(within(mobileMenu).getByText("Careers")).toBeDefined();

    // expect(within(mobileMenu).getByText('Events')).toBeDefined();

    const topLinkPartners = within(mobileMenu).getByText("Partners");
    expect(topLinkPartners).toBeDefined();
    fireEvent.click(topLinkPartners);
    expect(within(mobileMenu).getByText("Training Providers")).toBeDefined();

    expect(within(mobileMenu).getByText("About Us")).toBeDefined();
  });
});
