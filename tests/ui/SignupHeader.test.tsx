import { cleanup, render, screen } from "@testing-library/react";
import SignupHeader from "../../app/ui/SignupHeader";
import { afterEach, describe, expect, it } from "vitest";

describe("SignupHeader", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the header with the correct class name", () => {
    render(<SignupHeader className="test-class" />);
    const headerElement = screen.getByRole("banner");
    expect(headerElement.className).toBe("bg-white test-class");
  });

  it("renders the logo with correct alt text", () => {
    render(<SignupHeader />);
    const logoElement = screen.getByAltText("Tech Workforce Coalition");
    expect(logoElement).toBeDefined();
  });

  it("renders the link with correct href", () => {
    render(<SignupHeader />);
    const linkElement = screen.getByRole("link", {
      name: /Tech Workforce Coalition/i,
    });
    expect(linkElement).toHaveProperty("pathname", "/");
  });
});
