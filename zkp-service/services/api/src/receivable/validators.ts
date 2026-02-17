export type ValidationIssue = { code: string; message: string };

/**
 * Hook for field-specific business rules you’ll add later.
 * Return an array of issues (empty = ok).
 *
 * Examples you might add later:
 * - maturity_date must be >= now
 * - taxable_amount + tax_amount === total_amount_due
 * - currency_code must be in your allowlist
 */
export function runAdditionalChecks(
  key: string,
  raw: unknown
): ValidationIssue[] {
  // TODO: implement real checks per field key
  return [];
}
