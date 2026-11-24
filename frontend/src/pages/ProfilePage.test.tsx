import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";
import ProfilePage from "./ProfilePage";

vi.mock("../api", () => ({ api: vi.fn() }));
const mockedApi = vi.mocked(api);
afterEach(cleanup);

describe("ProfilePage research consent", () => {
  beforeEach(() => {
    mockedApi.mockImplementation(async <T,>(_path: string, options: RequestInit = {}) => {
      if (options.method === "PUT") {
        return {
          profile: {
            consent_research: true,
            consent_research_at: "2026-11-21T00:00:00+00:00",
          },
        } as T;
      }
      return null as T;
    });
  });

  it("defaults research consent to unchecked and keeps it optional", async () => {
    render(<ProfilePage />);
    const consent = await screen.findByRole("checkbox", {
      name: /Allow use of de-identified information for research/,
    });
    expect(consent).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Save profile" })).toBeEnabled();
  });

  it("reflects opt-in and its recorded timestamp after saving", async () => {
    render(<ProfilePage />);
    const consent = await screen.findByRole("checkbox", {
      name: /Allow use of de-identified information for research/,
    });
    fireEvent.click(consent);
    fireEvent.click(screen.getByRole("button", { name: "Save profile" }));
    expect(await screen.findByText(/Research consent recorded/)).toBeInTheDocument();
    expect(consent).toBeChecked();
  });
});
