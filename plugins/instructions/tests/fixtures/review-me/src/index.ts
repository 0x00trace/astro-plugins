import { buildServer } from "./server.js";

const server = buildServer();
await server.listen({ port: Number(process.env.PORT ?? 3000) });
