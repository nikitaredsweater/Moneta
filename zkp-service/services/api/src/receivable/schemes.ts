import { BASE_PUBLIC_FIELDS } from "./basePublic";
import { FIELD_CATALOG } from "./catalog";
import type { Scheme} from "./types";
import { Visibility } from "./types";

// Utility to expand base public fields into FieldUse entries
const basePublicUses = BASE_PUBLIC_FIELDS.map((key) => ({
  key,
  visibility: Visibility.PUBLIC,
  required: true,
}));

/**
 * Common receivable schemes. Each scheme:
 * - optionally inherits BASE_PUBLIC_FIELDS
 * - declares additional fields with public/private visibility
 */
export const SCHEMES: readonly Scheme[] = [
  {
    name: "standard_receivable_v1",
    version: "1.0",
    inheritsBasePublic: true,
    fields: [
      ...basePublicUses,
      { key: "taxable_amount", visibility: Visibility.PUBLIC, required: true },
      { key: "tax_amount", visibility: Visibility.PUBLIC, required: true },
      { key: "broker_id", visibility: Visibility.PUBLIC, required: false },
      { key: "invoice_id", visibility: Visibility.PRIVATE, required: true },
      {
        key: "ships_supplied_count",
        visibility: Visibility.PUBLIC,
        required: false,
      },
    ],
  },
  {
    name: "confidential_counterparties_v1",
    version: "1.0",
    inheritsBasePublic: true,
    fields: [
      ...basePublicUses,
      { key: "taxable_amount", visibility: Visibility.PUBLIC, required: true },
      { key: "tax_amount", visibility: Visibility.PUBLIC, required: true },
      { key: "broker_id", visibility: Visibility.PRIVATE, required: true },
      { key: "invoice_id", visibility: Visibility.PRIVATE, required: true },
      {
        key: "ships_supplied_count",
        visibility: Visibility.PUBLIC,
        required: false,
      },
    ],
  },
];

/**
 * Helper: validate a scheme against the catalog (keys exist, types known).
 */
export function validateSchemes(): string[] {
  const errors: string[] = [];
  for (const s of SCHEMES) {
    const seen = new Set<string>();
    for (const f of s.fields) {
      if (!FIELD_CATALOG[f.key])
        errors.push(`${s.name}: unknown field '${f.key}'`);
      if (seen.has(f.key)) errors.push(`${s.name}: duplicate field '${f.key}'`);
      seen.add(f.key);
    }
    for (const baseKey of BASE_PUBLIC_FIELDS) {
      if (
        !s.fields.some(
          (x) => x.key === baseKey && x.visibility === Visibility.PUBLIC
        )
      ) {
        errors.push(`${s.name}: missing base public field '${baseKey}'`);
      }
    }
  }
  return errors;
}
