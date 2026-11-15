// Applies the SQL files in migrations/ in order, once each.
import { readdir, readFile } from "node:fs/promises";
import pg from "pg";

const client = new pg.Client({ connectionString: process.env.DATABASE_URL });
await client.connect();
await client.query("create table if not exists schema_migrations (name text primary key)");
for (const name of (await readdir("migrations")).sort()) {
  const done = await client.query("select 1 from schema_migrations where name = $1", [name]);
  if (done.rowCount) continue;
  await client.query(await readFile(`migrations/${name}`, "utf8"));
  await client.query("insert into schema_migrations (name) values ($1)", [name]);
}
await client.end();
