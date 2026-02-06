import React from "react";
import { cleanup, render, screen } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import Footer from "../../app/ui/Footer";

vi.mock("next/link", () => ({
  default: ({ children, ...props }: { children: React.ReactNode }) => (
    <a {...props}>{children}</a>
  ),
}));

vi.mock("next/image", () => ({
  default: (props: any) => <img {...props} />,
}));

describe("Footer", () => {
  beforeEach(() => {
    render(<Footer />);
  });

  afterEach(() => {
    cleanup();
  });

  it("renders the Tech Workforce Coalition logo", () => {
    const logo = screen.getByAltText("Tech Workforce Coalition");
    expect(logo).toBeDefined();
    expect(logo.getAttribute("src")).toBe("/images/TWC-alt-white.svg");
    expect(logo.getAttribute("width")).toBe("69");
    expect(logo.getAttribute("height")).toBe("27.24");
  });

  it("renders the LinkedIn link", () => {
    const linkedinLink = screen.getByText("Follow Us:").closest("a");
    expect(linkedinLink?.getAttribute("href")).toBe(
      "https://www.linkedin.com/company/washington-tech-workforce-coalition",
    );
    expect(linkedinLink?.getAttribute("target")).toBe("_blank");

    const linkedinIcon = screen.getByAltText("Linkedin Link");
    expect(linkedinIcon).toBeDefined();
    expect(linkedinIcon.getAttribute("src")).toBe(
      "/images/stock/linkedin-black.png",
    );
    expect(linkedinIcon.getAttribute("width")).toBe("22");
  });

  it("renders the Privacy Policy link", () => {
    const privacyLink = screen.getByText("Terms of Services");
    expect(privacyLink.getAttribute("href")).toBe("/policies/terms-of-service");
  });
});
