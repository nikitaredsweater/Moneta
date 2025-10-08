import { Router, type Request, type Response } from "express";
import {
  FIELD_CATALOG,
  BASE_PUBLIC_FIELDS,
  SCHEMES,
  validateSchemes,
  type FieldSpec,
  type Scheme,
} from "../receivable";

const router = Router();

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

export default router;
