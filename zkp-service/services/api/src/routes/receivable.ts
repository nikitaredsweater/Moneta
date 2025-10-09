import { Router, type Request, type Response } from "express";
import {
  FIELD_CATALOG,
  BASE_PUBLIC_FIELDS,
  SCHEMES,
  validateSchemes,
  type FieldSpec,
  type Scheme,
  Visibility,
  encodeValue,
  runAdditionalChecks,
} from "../receivable";
import { generateSalt, computePoseidonCommitment } from "../utils/commitment";
import { generateWitnessSimple, prepareCircuitInput } from "../utils/witness";

const router = Router();

////////////////////             helpers             ///////////////////////////

const b2s = (v: unknown) => (typeof v === "bigint" ? v.toString() : v);

// Fail fast on bad config at startup
const configErrors = validateSchemes();
if (configErrors.length) {
  // You can throw to crash the process, or log & continue.
  // Throwing is safer in infra.
  throw new Error(
    "Receivable scheme config errors:\n" + configErrors.join("\n")
  );
}

// Helper: expand a scheme with catalog info so clients see expected types, etc.
function expandScheme(s: Scheme) {
  const expandedFields = s.fields.map((f) => {
    const spec: FieldSpec | undefined = FIELD_CATALOG[f.key];
    return {
      key: f.key,
      visibility: f.visibility,
      required: f.required ?? true,
      // Spec details (expected type/scale/description/nameId)
      type: spec?.type ?? null,
      scale: spec?.scale ?? null,
      nameId: spec ? b2s(spec.nameId) : null,
      description: spec?.description ?? null,
    };
  });

  return {
    name: s.name,
    version: s.version,
    inheritsBasePublic: !!s.inheritsBasePublic,
    fields: expandedFields,
  };
}

function getSchemeOrNull(name: string): Scheme | undefined {
  return SCHEMES.find((s) => s.name === name);
}

type VisibilityLiteral = "public" | "private";
function toEnumVisibility(v: VisibilityLiteral): Visibility {
  return v === "public" ? Visibility.PUBLIC : Visibility.PRIVATE;
}
function isVisibilityLiteral(x: unknown): x is VisibilityLiteral {
  return x === "public" || x === "private";
}

////////////////////       metadata endpoints       ////////////////////////////

/**
 * GET /receivable/fields
 * -> Full catalog of supported fields with types (expected encoding for templates)
 */
router.get("/fields", (_req: Request, res: Response) => {
  const fields = Object.values(FIELD_CATALOG).map((f) => ({
    key: f.key,
    nameId: b2s(f.nameId), // send as string to avoid JSON bigint issues
    type: f.type,
    scale: f.scale ?? null,
    description: f.description ?? null,
  }));
  res.status(200).json({ fields });
});

/**
 * GET /receivable/base-public
 * -> The minimal set of public fields every scheme must include
 */
router.get("/base-public", (_req: Request, res: Response) => {
  res.status(200).json({ basePublic: BASE_PUBLIC_FIELDS });
});

/**
 * GET /receivable/schemes
 * -> All supported schemes with expected field visibilities and types
 */
router.get("/schemes", (_req: Request, res: Response) => {
  res.status(200).json({
    schemes: SCHEMES.map(expandScheme),
  });
});

/**
 * GET /receivable/schemes/:name
 * -> One scheme (expanded) by name
 */
router.get("/schemes/:name", (req: Request, res: Response) => {
  const scheme = SCHEMES.find((s) => s.name === req.params.name);
  if (!scheme) return res.status(404).json({ error: "scheme_not_found" });

  res.status(200).json({ scheme: expandScheme(scheme) });
});

//////////////////// creation / validation endpoint ////////////////////////////

/**
 * POST /receivable/create
 * Body:
 * {
 *   "scheme": "standard_receivable_v1",
 *   "fields": {
 *     "maturity_date": { "value": 1720051200, "visibility": "public" },
 *     "currency_code": { "value": 840, "visibility": "public" },
 *     "total_amount_due": { "value": "100000.000000", "visibility": "public" },
 *     "taxable_amount": { "value": "90000.000000", "visibility": "public" },
 *     "tax_amount": { "value": "10000.000000", "visibility": "public" },
 *     "invoice_id": { "value": "c8f6cf7a-1a17-4f7a-8dc2-0b2b4b5b1b0f", "visibility": "private" }
 *   }
 * }
 *
 * Rules:
 * - scheme must be one of the supported SCHEMES (no custom schemes)
 * - no unknown field keys
 * - required fields must be present
 * - provided visibility must exactly match scheme's visibility for that field
 * - provided values must conform to FieldSpec types (via encodeValue)
 * - runAdditionalChecks() hook for future business rules
 */
router.post("/create", async (req: Request, res: Response) => {
  const body = req.body as {
    scheme?: string;
    fields?: Record<string, { value: unknown; visibility: unknown }>;
  };

  // quick shape checks
  if (!body || typeof body !== "object") {
    return res.status(400).json({ error: "invalid_body" });
  }
  if (!body.scheme || typeof body.scheme !== "string") {
    return res.status(400).json({ error: "scheme_required" });
  }
  const scheme = getSchemeOrNull(body.scheme);
  if (!scheme) {
    return res.status(400).json({ error: "unsupported_scheme" });
  }
  if (!body.fields || typeof body.fields !== "object") {
    return res.status(400).json({ error: "fields_required" });
  }

  const inputKeys = Object.keys(body.fields);

  // 1) Unknown field keys (not in catalog)
  const unknownKeys = inputKeys.filter((k) => !FIELD_CATALOG[k]);
  if (unknownKeys.length) {
    return res
      .status(400)
      .json({ error: "unknown_fields", details: unknownKeys });
  }

  // 2) Extras not in scheme (disallow for now)
  const schemeKeys = new Set(scheme.fields.map((f) => f.key));
  const extras = inputKeys.filter((k) => !schemeKeys.has(k));
  if (extras.length) {
    return res
      .status(400)
      .json({ error: "fields_not_in_scheme", details: extras });
  }

  // 3) Required fields present
  const missingRequired = scheme.fields
    .filter((f) => f.required ?? true)
    .map((f) => f.key)
    .filter((k) => !(k in body.fields!));
  if (missingRequired.length) {
    return res
      .status(400)
      .json({ error: "missing_required_fields", details: missingRequired });
  }

  // 4) Visibility must match scheme
  const visErrors: string[] = [];
  for (const f of scheme.fields) {
    const provided = body.fields[f.key];
    if (!provided) continue; // optional & absent is fine
    const v = provided.visibility;
    if (!isVisibilityLiteral(v)) {
      visErrors.push(
        `${f.key}: invalid visibility (expected 'public'|'private')`
      );
      continue;
    }
    if (toEnumVisibility(v) !== f.visibility) {
      visErrors.push(
        `${
          f.key
        }: visibility mismatch (expected '${f.visibility.toLowerCase()}')`
      );
    }
  }
  if (visErrors.length) {
    return res
      .status(400)
      .json({ error: "visibility_mismatch", details: visErrors });
  }

  // 5) Type/format check via encodeValue + custom validators
  const formatErrors: string[] = [];
  for (const key of inputKeys) {
    const spec = FIELD_CATALOG[key]!;
    const { value } = body.fields[key]!;
    try {
      // Try to encode (throws on bad format/type)
      void encodeValue(spec, value);
    } catch (e) {
      formatErrors.push(
        `${key}: ${e instanceof Error ? e.message : "invalid_value"}`
      );
      continue;
    }
    // Additional project-specific checks (currently stubbed)
    const issues = runAdditionalChecks(key, value);
    if (issues.length) {
      for (const iss of issues)
        formatErrors.push(`${key}: ${iss.code} - ${iss.message}`);
    }
  }
  if (formatErrors.length) {
    return res
      .status(400)
      .json({ error: "invalid_field_values", details: formatErrors });
  }

  // 6) Ensure "required public fields" are indeed public in input
  const requiredPublic = scheme.fields.filter(
    (f) => (f.required ?? true) && f.visibility === Visibility.PUBLIC
  );
  const notPublic: string[] = [];
  for (const f of requiredPublic) {
    const provided = body.fields[f.key];
    if (!provided) continue; // already handled by missingRequired
    if (provided.visibility !== "public") {
      notPublic.push(f.key);
    }
  }
  if (notPublic.length) {
    return res
      .status(400)
      .json({ error: "required_fields_not_public", details: notPublic });
  }

  // If we reach here, the payload is valid for this scheme

  // Encoding values
  const encoded: bigint[] = []; // we need to maintain the order of the fields!
  for (const [key, _] of Object.entries(body.fields)) {
    const spec = FIELD_CATALOG[key];
    const { value } = body.fields[key]!;
    if (!spec) {
      return res.status(400).json({ error: "unknown_field", details: key });
    }
    encoded.push(encodeValue(spec, value));
  }

  // Salt + Poseidon hash
  const salt = generateSalt();
  const commitment = await computePoseidonCommitment(encoded, salt);

  // Making input.json file

  // export interface WitnessGenerationConfig {
  //   /** Name of the circuit (e.g., "ReceivableProofNamed") */
  //   circuitName: string;
  //   /** Path to the compiled circuit directory (default: "./circuits") */
  //   circuitsDir?: string;
  //   /** Path to input.json (default: "./input.json") */
  //   inputJsonPath?: string;
  //   /** Output path for witness file (default: "./witness.wtns") */
  //   outputWitnessPath?: string;
  // }
  const result = await prepareCircuitInput(req.body, "./input.json");
  const witnessResult = await generateWitnessSimple({
    circuitName: "receivable_mvp",
    inputJsonPath: "../../input.json",
    circuitsDir: "../../../../circuits/src",
    outputWitnessPath: "./witness.wtns",
  }); // default circuit option for MVP
  console.log(witnessResult); // testing

  return res.status(200).json(result);
});

export default router;
