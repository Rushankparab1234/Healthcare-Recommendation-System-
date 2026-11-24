import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("api", () => {
  it("does not parse an empty 204 response as JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(null, {
      status: 204,
      headers: { "content-type": "application/json" },
    }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(api<void>("/api/v1/providers/demo/save", { method: "DELETE" }))
      .resolves.toBeUndefined();
  });
});
