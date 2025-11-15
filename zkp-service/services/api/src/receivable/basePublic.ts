// Minimum public fields every scheme MUST expose
export const BASE_PUBLIC_FIELDS: readonly string[] = [
  "maturity_date",
  "currency_code",
  "total_amount_due",
] as const;
