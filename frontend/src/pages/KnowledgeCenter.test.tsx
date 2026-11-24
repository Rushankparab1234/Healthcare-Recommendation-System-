import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "../api";
import KnowledgeCenter from "./KnowledgeCenter";

vi.mock("../api", () => ({ api: vi.fn() }));
const mockedApi = vi.mocked(api);

const articles = [{
  id: "medlineplus-cough",
  title: "Cough",
  category: "Respiratory health",
  source_name: "MedlinePlus",
  source_url: "https://medlineplus.gov/cough.html",
  content: "Coughs can be acute or chronic.",
  reviewed_at: "2026-11-21",
}];

describe("KnowledgeCenter", () => {
  beforeEach(() => {
    mockedApi.mockImplementation(async (path) => {
      if (path === "/api/v1/knowledge/categories") return ["Respiratory health"] as never;
      return articles as never;
    });
  });

  it("renders sourced articles and submits search filters", async () => {
    render(<MemoryRouter><KnowledgeCenter /></MemoryRouter>);
    expect(await screen.findByRole("link", { name: "Cough" })).toHaveAttribute("href", "/knowledge/medlineplus-cough");
    expect(screen.getByRole("link", { name: "MedlinePlus" })).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Search articles"), { target: { value: "cough" } });
    fireEvent.change(screen.getByLabelText("Category"), { target: { value: "Respiratory health" } });
    fireEvent.click(screen.getByRole("button", { name: /search/i }));

    await waitFor(() => expect(mockedApi).toHaveBeenCalledWith(
      "/api/v1/knowledge?search=cough&category=Respiratory+health",
    ));
  });

  it("shows a clear error when the knowledge endpoint fails", async () => {
    mockedApi.mockRejectedValue(new Error("Knowledge API unavailable"));
    render(<MemoryRouter><KnowledgeCenter /></MemoryRouter>);
    expect(await screen.findByRole("alert")).toHaveTextContent("Knowledge API unavailable");
  });
});
