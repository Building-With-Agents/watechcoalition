import {
  render,
  screen,
  fireEvent,
  waitFor,
  cleanup,
  act,
} from "@testing-library/react";
import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import AvatarUpload from "../../../app/ui/components/AvatarUpload";

const mockOnImageUpload = vi.fn();

const defaultProps = {
  id: "avatar-upload",
  fileTypeText: "PNG, JPG",
  accept: ".png,.jpg",
  maxSizeMB: 5,
  userId: "user123",
  onImageUpload: mockOnImageUpload,
  initialImageUrl: "http://example.com/initial-avatar.png",
  disabled: false,
  apiPath: "/api/users/avatar/upload",
};

describe("AvatarUpload", () => {
  beforeEach(() => {
    global.URL.createObjectURL = vi.fn();
    global.URL.revokeObjectURL = vi.fn();
    File.prototype.arrayBuffer = vi.fn().mockResolvedValue(new ArrayBuffer(8));
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });
    render(<AvatarUpload {...defaultProps} />);
  });
  afterEach(() => {
    cleanup();
  });

  it("should render initial image", () => {
    const avatarDiv = screen.getByTestId("avatar-image");
    const img = avatarDiv.querySelector("img");
    expect(img?.getAttribute("src")).toBe(defaultProps.initialImageUrl);
  });

  it("should handle file upload", async () => {
    const file = new File(["avatar"], "avatar.png", { type: "image/png" });

    const input = screen.getByLabelText(/upload image/i);
    fireEvent.change(input, { target: { files: [file] } });

    await waitFor(
      () => {
        expect(mockOnImageUpload).toHaveBeenCalled();
      },
      { timeout: 2000 },
    );
  });

  it("should show error for file size exceeded", async () => {
    const largeFile = new File(
      ["a".repeat(6 * 1024 * 1024)],
      "large-avatar.png",
      { type: "image/png" },
    );

    const input = screen.getByLabelText(/upload image/i);
    fireEvent.change(input, { target: { files: [largeFile] } });

    await waitFor(
      () => {
        expect(screen.getByText(/file is too large:/i)).toBeDefined();
      },
      { timeout: 2000 },
    );
  });

  it("should show error for unsupported file type", async () => {
    const unsupportedFile = new File(["avatar"], "avatar.gif", {
      type: "image/gif",
    });

    const input = screen.getByLabelText(/upload image/i);
    fireEvent.change(input, { target: { files: [unsupportedFile] } });

    await waitFor(
      () => {
        expect(screen.getByText(/unsupported file type/i)).toBeDefined();
      },
      { timeout: 2000 },
    );
  });
});
