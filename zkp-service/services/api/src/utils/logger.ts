import winston from "winston";
import path from "path";
import fs from "fs";

// Environment configuration with defaults matching moneta-logging conventions
const LOG_LEVEL = process.env.LOG_LEVEL?.toLowerCase() || "info";
const LOG_OUTPUT = process.env.LOG_OUTPUT?.toLowerCase() || "console";
const LOG_FILE_PATH = process.env.LOG_FILE_PATH || "logs/zkp_service.log";

// Performance thresholds (matching Python moneta-logging)
export const SLOW_REQUEST_THRESHOLD_MS = 1000;
export const VERY_SLOW_REQUEST_THRESHOLD_MS = 5000;

// Log format matching docs/logging.md:
// [COMPONENT] Action description | key1=value1 | key2=value2
const logFormat = winston.format.combine(
  winston.format.timestamp({
    format: "YYYY-MM-DD HH:mm:ss",
  }),
  winston.format.printf(({ timestamp, level, message }) => {
    return `${timestamp} | ${level.toUpperCase().padEnd(8)} | ${message}`;
  })
);

// Console format with colors
const consoleFormat = winston.format.combine(
  winston.format.colorize(),
  winston.format.timestamp({
    format: "YYYY-MM-DD HH:mm:ss",
  }),
  winston.format.printf(({ timestamp, level, message }) => {
    return `${timestamp} | ${level.padEnd(15)} | ${message}`;
  })
);

// Build transports based on LOG_OUTPUT
const transports: winston.transport[] = [];

if (LOG_OUTPUT === "console" || LOG_OUTPUT === "both") {
  transports.push(
    new winston.transports.Console({
      format: consoleFormat,
    })
  );
}

if (LOG_OUTPUT === "file" || LOG_OUTPUT === "both") {
  // Ensure log directory exists
  const logDir = path.dirname(LOG_FILE_PATH);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  transports.push(
    new winston.transports.File({
      filename: LOG_FILE_PATH,
      format: logFormat,
      maxsize: 10 * 1024 * 1024, // 10MB rotation
      maxFiles: 5,
    })
  );
}

// Fallback to console if no transports configured
if (transports.length === 0) {
  transports.push(
    new winston.transports.Console({
      format: consoleFormat,
    })
  );
}

const logger = winston.createLogger({
  level: LOG_LEVEL,
  transports,
});

// Log startup configuration
logger.info(
  `[SYSTEM] Logger initialized | level=${LOG_LEVEL} | output=${LOG_OUTPUT} | file_path=${LOG_FILE_PATH}`
);

// Global error handlers
process.on("unhandledRejection", (reason) => {
  logger.error(`[SYSTEM] Unhandled Rejection | error=${reason}`);
});

process.on("uncaughtException", (err) => {
  logger.error(
    `[SYSTEM] Uncaught Exception | error_type=${err.name} | error=${err.message}`
  );
});

export default logger;
