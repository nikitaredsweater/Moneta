import crypto from "crypto";
import * as circomlibjs from "circomlibjs";

// FIXME: This code introduces a light code duplication
// (look at the routes/receivable.ts)

/** Generate a secure 256-bit salt (as bigint) */
export function generateSalt(): bigint {
  return BigInt("0x" + crypto.randomBytes(32).toString("hex"));
}

/**
 * Compute field hash: Poseidon(nameId, value)
 */
async function computeFieldHash(
  nameId: bigint,
  value: bigint
): Promise<bigint> {
  const poseidon = await circomlibjs.buildPoseidon();
  const hash = poseidon.F.toObject(poseidon([nameId, value]));
  return BigInt(hash);
}

/**
 * Compute a Poseidon commitment over the given field values and salt.
 * All values must already be bigint-encoded (using your encodeValue helpers).
 */
export async function computePoseidonCommitment(
  fieldValues: bigint[],
  salt: bigint
): Promise<bigint> {
  const poseidon = await circomlibjs.buildPoseidon();
  const input = [...fieldValues, salt]; // data || salt
  const hash = poseidon.F.toObject(poseidon(input));
  return BigInt(hash);
}

/**
 * Compute the commitment matching the circuit structure:
 * commitment = Poseidon(hash(name1, value1), hash(name2, value2), ..., salt)
 */
export async function computePoseidonCommitmentSeparate(
  fields: Array<{ nameId: bigint; value: bigint }>,
  salt: bigint
): Promise<bigint> {
  const poseidon = await circomlibjs.buildPoseidon();

  // First, hash each (name, value) pair
  const fieldHashes: bigint[] = [];
  for (const field of fields) {
    const hash = await computeFieldHash(field.nameId, field.value);
    fieldHashes.push(hash);
  }

  // Then hash all field hashes with the salt
  const input = [...fieldHashes, salt];
  const hash = poseidon.F.toObject(poseidon(input));
  return BigInt(hash);
}
