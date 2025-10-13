import express from "express"
import type { Request, Response } from "express";
import receivableRouter from "./routes/receivable";
import morgan from "morgan";
import logger from "./utils/logger";

const app = express();

// Parse JSON bodies (increase limit if you like)
app.use(express.json({ limit: "1mb" }));

// Log HTTP requests
app.use(
  morgan("dev", {
    stream: {
      write: (message) => logger.info(message.trim()),
    },
  })
);

// Healthcheck
app.get("/health", (_req: Request, res: Response) =>
  res.status(200).send("ok")
);

// Custom routes
app.use("/receivable", receivableRouter);

// Minimal endpoint: log incoming JSON
app.post("/ingest", (req: Request, res: Response) => {
  console.log("Received JSON:", req.body);
  res.sendStatus(204); // No Content
});

const PORT = Number(process.env.PORT ?? 3000);
app.listen(PORT, "0.0.0.0", () => {
  console.log(`API listening on http://0.0.0.0:${PORT}`);
});
