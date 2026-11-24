import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";
import type { Provider } from "../types";
import ProviderDirectory from "./ProviderDirectory";

vi.mock("../api", () => ({ api: vi.fn() }));
const mockedApi = vi.mocked(api);

const provider: Provider = {
  id: "demo-provider-1",
  name: "Harbor General Clinic",
  specialty: "General Medicine",
  location: "Mumbai",
  consultation_type: "in-person",
  is_demo: true,
  verification_status: "synthetic demo — not verified",
  qualification_information: "Synthetic demo record.",
  availability: {
    demo_signal: 0.8,
    is_bookable: false,
    description: "Synthetic signal only.",
  },
};

describe("ProviderDirectory saved state", () => {
  let saved: boolean;

  beforeEach(() => {
    saved = false;
    mockedApi.mockImplementation(async <T,>(path: string, options: RequestInit = {}) => {
      if (path === "/api/v1/providers") return [provider] as T;
      if (path === "/api/v1/specialties") return [{ name: provider.specialty }] as T;
      if (path === "/api/v1/patients/me/dashboard") {
        return { saved_providers: saved ? [provider] : [] } as T;
      }
      if (path.endsWith("/save") && options.method === "POST") {
        saved = true;
        return { status: "saved" } as T;
      }
      if (path.endsWith("/save") && options.method === "DELETE") {
        saved = false;
        return undefined as T;
      }
      throw new Error(`Unexpected API request: ${path}`);
    });
  });

  it("uses the saved/unsave control labels and restores state after remount", async () => {
    const firstRender = render(<MemoryRouter><ProviderDirectory /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Save Harbor General Clinic" }));
    expect(await screen.findByRole("button", { name: "Unsave Harbor General Clinic" })).toHaveTextContent("Saved");
    expect(mockedApi).toHaveBeenCalledWith(
      "/api/v1/providers/demo-provider-1/save",
      { method: "POST" },
    );

    firstRender.unmount();
    render(<MemoryRouter><ProviderDirectory /></MemoryRouter>);
    fireEvent.click(await screen.findByRole("button", { name: "Unsave Harbor General Clinic" }));
    expect(await screen.findByRole("button", { name: "Save Harbor General Clinic" })).toHaveTextContent("Save");
    expect(mockedApi).toHaveBeenCalledWith(
      "/api/v1/providers/demo-provider-1/save",
      { method: "DELETE" },
    );
  });
});
