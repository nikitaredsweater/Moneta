import { FieldSpec, FieldType } from "./types";

const UUID_V4_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

/** Canonical: lower-case, strip hyphens, big-endian 128-bit -> BigInt */
export function encodeUuidV4(uuid: string): bigint {
  if (!UUID_V4_RE.test(uuid)) {
    throw new Error("invalid_uuidv4");
  }
  const hex = uuid.replace(/-/g, "").toLowerCase(); // 32 hex chars
  return BigInt("0x" + hex); // fits easily in BN254 field element
}

/** Example scaler for FP6 monetary amounts (string/number -> BigInt) */
export function encodeFp6(x: string | number, scale = 1e6): bigint {
  if (typeof x === "number") {
    return BigInt(Math.round(x * scale));
  }
  // string: allow decimal like "123.456789"
  const [int = "0", frac = ""] = x.split(".");
  const fracPadded = (frac + "0".repeat(6)).slice(0, 6);
  return BigInt(int + fracPadded);
}

/** Generic value encoder using the catalog spec */
export function encodeValue(spec: FieldSpec, raw: unknown): bigint {
  switch (spec.type) {
    case FieldType.UUID:
      if (typeof raw !== "string") throw new Error("uuid_must_be_string");
      return encodeUuidV4(raw);
    case FieldType.FP6:
      if (typeof raw !== "string" && typeof raw !== "number")
        throw new Error("fp6_bad_type");
      return encodeFp6(raw, spec.scale ?? 1e6);
    case FieldType.UINT64:
    case FieldType.ENUM:
    case FieldType.TIMESTAMP:
      if (
        typeof raw !== "number" &&
        typeof raw !== "bigint" &&
        typeof raw !== "string"
      ) {
        throw new Error("numeric_expected");
      }
      return BigInt(raw as any);
    case FieldType.BOOL:
      if (typeof raw !== "boolean") throw new Error("bool_expected");
      return raw ? 1n : 0n;
    case FieldType.BYTES32:
      if (typeof raw !== "string") throw new Error("bytes32_hex_expected");
      return BigInt(raw); // expects 0x… hex
    default:
      throw new Error("unsupported_field_type");
  }
}
