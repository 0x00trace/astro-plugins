import { describe, expect, it } from "vitest";
import { buildServer } from "../src/server.js";

describe("health", () => {
  it("answers ok", async () => {
    const response = await buildServer().inject({ method: "GET", url: "/health" });
    expect(response.json()).toEqual({ ok: true });
  });
});
