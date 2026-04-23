export class SentinelError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SentinelError";
  }
}

export class AuthError extends SentinelError {
  constructor(message: string) {
    super(message);
    this.name = "AuthError";
  }
}

export class RateLimitError extends SentinelError {
  readonly retryAfterSeconds: number | null;

  constructor(message: string, retryAfterSeconds: number | null = null) {
    super(message);
    this.name = "RateLimitError";
    this.retryAfterSeconds = retryAfterSeconds;
  }
}

export class TimeoutError extends SentinelError {
  constructor(message: string) {
    super(message);
    this.name = "TimeoutError";
  }
}

export class ServerError extends SentinelError {
  readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ServerError";
    this.statusCode = statusCode;
  }
}
