import Fastify from "fastify";
import { registerHandlers } from "./api/handlers.js";
import { AppError } from "./lib/errors.js";

export function buildServer() {
  const server = Fastify({ logger: true });
  server.setErrorHandler((error, _request, reply) => {
    if (error instanceof AppError) return reply.status(error.status).send({ error: error.code });
    server.log.error(error);
    return reply.status(500).send({ error: "internal" });
  });
  registerHandlers(server);
  return server;
}
