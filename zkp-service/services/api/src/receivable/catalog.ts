import type { FieldSpec} from "./types";
import { FieldType } from "./types";

/**
 * NOTE: nameId values are stable numeric IDs used in your Circom "named fields" circuit.
 * For MVP we assign fixed small integers. In production, switch to PoseidonHash("field_key")
 * (kept constant once published).
 */
export const FIELD_CATALOG: Record<string, FieldSpec> = {
  maturity_date: {
    key: "maturity_date",
    nameId: 1n,
    type: FieldType.TIMESTAMP,
    description: "Unix timestamp (seconds) when the receivable matures",
  },
  currency_code: {
    key: "currency_code",
    nameId: 2n,
    type: FieldType.ENUM, // ISO 4217 numeric (e.g., USD=840, EUR=978)
    description: "ISO 4217 numeric currency code",
  },
  total_amount_due: {
    key: "total_amount_due",
    nameId: 3n,
    type: FieldType.FP6,
    scale: 1e6,
    description: "Total amount due, fixed-point 1e6",
  },
  taxable_amount: {
    key: "taxable_amount",
    nameId: 4n,
    type: FieldType.FP6,
    scale: 1e6,
  },
  tax_amount: {
    key: "tax_amount",
    nameId: 5n,
    type: FieldType.FP6,
    scale: 1e6,
  },
  broker_id: {
    key: "broker_id",
    nameId: 6n,
    type: FieldType.BYTES32, // pass as 0x… → bigint
  },
  invoice_id: {
    key: "invoice_id",
    nameId: 7n,
    type: FieldType.BYTES32,
  },
  ships_supplied_count: {
    key: "ships_supplied_count",
    nameId: 8n,
    type: FieldType.UINT64,
  },
};
