import { expect, it } from "vitest";
import { buildServer } from "../../src/server.js";

it("books an entry on a new account", async () => {
  const server = buildServer();
  const account = await server.inject({ method: "POST", url: "/accounts", payload: { name: "Cash" } });
  const { id } = account.json();
  const entry = await server.inject({
    method: "POST",
    url: `/accounts/${id}/entries`,
    payload: { amountCents: -1250, bookedOn: "2026-01-31" },
  });
  expect(entry.json()).toEqual({ ok: true });
});
