import { cleanup, render, screen } from "@testing-library/react";
import Avatar from "../../../app/ui/components/Avatar";
import { vi, afterEach, describe, expect, it } from "vitest";

vi.mock("next/image", () => ({
  default: (props: any) => <img {...props} />,
}));

describe("Avatar", () => {
  afterEach(() => {
    cleanup();
  });

  it("renders the image with the correct src, size, and alt attributes", () => {
    render(<Avatar imgsrc="test-image.jpg" />);
    const imageElement = screen.getByAltText("") as HTMLImageElement;
    expect(imageElement.src).toContain("test-image.jpg");
    expect(imageElement).toHaveProperty("alt", "");
    expect(imageElement).toHaveProperty("width", 85);
    expect(imageElement).toHaveProperty("height", 85);
  });

  it("renders the default icon when imgsrc is undefined", () => {
    render(<Avatar imgsrc={undefined} />);
    const iconElement = screen.getByTestId("default-avatar-icon");

    expect(iconElement).toBeDefined();
  });

  it("renders the avatar at 2x scale", () => {
    render(<Avatar imgsrc="test-image.jpg" scale={2} />);
    const imageElement = screen.getByAltText("") as HTMLImageElement;
    expect(imageElement.src).toContain("test-image.jpg");
    expect(imageElement).toHaveProperty("width", 170);
    expect(imageElement).toHaveProperty("height", 170);
  });
});
