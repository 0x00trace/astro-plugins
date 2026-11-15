import type { FastifyInstance } from "fastify";
import { query } from "../lib/db.js";
import { notFound } from "../lib/errors.js";
import { NewAccount, NewEntry } from "./schemas.js";

export function registerHandlers(server: FastifyInstance) {
  server.get("/health", async () => ({ ok: true }));

  server.post("/accounts", async (request) => {
    const body = NewAccount.parse(request.body);
    const rows = await query("insert into accounts (name) values ($1) returning id", [body.name]);
    return { id: rows[0].id };
  });

  server.post<{ Params: { id: string } }>("/accounts/:id/entries", async (request) => {
    const body = NewEntry.parse(request.body);
    const account = await query("select id from accounts where id = $1", [request.params.id]);
    if (account.length === 0) throw notFound("account");
    await query(
      "insert into entries (account_id, amount_cents, booked_on) values ($1, $2, $3)",
      [request.params.id, body.amountCents, body.bookedOn],
    );
    return { ok: true };
  });

  server.get<{ Params: { id: string } }>("/accounts/:id/totals", async (request) => {
    const account = await query("select id from accounts where id = $1", [request.params.id]);
    if (account.length === 0) throw notFound("account");
    const rows = await query(
      `select to_char(booked_on, 'YYYY-MM') as month, sum(amount_cents)::int as total_cents
       from entries where account_id = $1 group by 1 order by 1`,
      [request.params.id],
    );
    return { totals: rows };
  });
}
