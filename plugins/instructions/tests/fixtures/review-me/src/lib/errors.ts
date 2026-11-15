// The error handler in server.ts maps only AppError to a status; anything else is a 500.
export class AppError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
  ) {
    super(code);
  }
}

export const notFound = (what: string) => new AppError(404, `${what}_not_found`);
export const badRequest = (code: string) => new AppError(400, code);
