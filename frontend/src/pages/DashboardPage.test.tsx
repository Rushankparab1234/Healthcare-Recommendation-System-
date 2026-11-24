import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";
import DashboardPage from "./DashboardPage";

vi.mock("../api", () => ({ api: vi.fn() }));
const mockedApi = vi.mocked(api);

describe("DashboardPage", () => {
  beforeEach(() => {
    mockedApi.mockResolvedValue({
      assessment_count: 2,
      recommendation_count: 1,
      saved_provider_count: 0,
      profile_completion: { completed: 2, total: 6, percentage: 33 },
      recent_assessments: [{
        id: "assessment-1",
        created_at: "2026-11-21T00:00:00Z",
        severity: "moderate",
        emergency: false,
        symptoms: ["cough"],
      }],
      recent_recommendations: [],
      saved_providers: [],
      recent_activity: [],
    });
  });

  it("renders patient-scoped counts, history, and profile completion from the dashboard API", async () => {
    render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    expect(await screen.findByText("2", { selector: "strong" })).toBeInTheDocument();
    expect(screen.getByText("1", { selector: "strong" })).toBeInTheDocument();
    expect(screen.getByText("33%", { selector: "strong" })).toBeInTheDocument();
    expect(screen.getByText("cough")).toBeInTheDocument();
    expect(mockedApi).toHaveBeenCalledWith("/api/v1/patients/me/dashboard");
  });

  it("renders typed recommendation details instead of stringifying result objects", async () => {
    const createdAt = "2026-11-21T00:00:00Z";
    mockedApi.mockResolvedValue({
      assessment_count: 1,
      recommendation_count: 1,
      saved_provider_count: 0,
      profile_completion: { completed: 0, total: 6, percentage: 0 },
      recent_assessments: [],
      recent_recommendations: [{
        id: "recommendation-42",
        created_at: createdAt,
        items: [
          {
            provider_id: "provider-1",
            provider_name: "Harbor General Clinic",
            specialty: "General Medicine",
            rank: 1,
            explanation: "Best location and consultation match.",
          },
          {
            provider_id: "provider-2",
            provider_name: "Riverheart Demo Clinic",
            specialty: "Cardiology",
            rank: 2,
            explanation: "Second-ranked compatible demo provider.",
          },
        ],
      }],
      saved_providers: [],
      recent_activity: [],
    });

    const { container } = render(<MemoryRouter><DashboardPage /></MemoryRouter>);
    const formattedDate = new Date(createdAt).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
    expect(await screen.findByText("Recommendation ID: recommendation-42")).toBeInTheDocument();
    expect(screen.getByText("#1 Harbor General Clinic")).toBeInTheDocument();
    expect(screen.getByText("General Medicine")).toBeInTheDocument();
    expect(screen.getByText("Best location and consultation match.")).toBeInTheDocument();
    expect(screen.getByText("#2 Riverheart Demo Clinic")).toBeInTheDocument();
    expect(screen.getByText(formattedDate)).toBeInTheDocument();
    expect(container).not.toHaveTextContent("[object Object]");
  });
});
