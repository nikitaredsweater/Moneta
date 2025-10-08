export enum FieldType {
  UINT64 = "uint64", // non-negative integers (≤ 2^64-1)
  BOOL = "bool",
  FP6 = "fp6", // fixed-point with 1e6 scale (store as integer)
  TIMESTAMP = "timestamp", // unix seconds
  BYTES32 = "bytes32", // 32-byte identifier, passed as bigint/hex→bigint
  ENUM = "enum", // small integer code (e.g., ISO 4217 numeric)
}

export interface FieldSpec {
  key: string; // canonical key (stable)
  nameId: bigint; // numeric ID used in-circuit for the field name
  type: FieldType;
  scale?: number; // for FP6 = 1e6; optional for others
  description?: string;
}

export enum Visibility {
  PUBLIC = "public", // will be used in both private and public segments of the template
  PRIVATE = "private",
}

export interface FieldUse {
  key: string;
  visibility: Visibility;
  required?: boolean; // default true in most schemes
}

export interface Scheme {
  name: string;
  version: string;
  inheritsBasePublic?: boolean;
  fields: FieldUse[]; // add/override visibilities
}
