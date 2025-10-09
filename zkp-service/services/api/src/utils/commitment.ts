import crypto from "crypto";
import * as circomlibjs from "circomlibjs";

/** Generate a secure 256-bit salt (as bigint) */
export function generateSalt(): bigint {
  return BigInt("0x" + crypto.randomBytes(32).toString("hex"));
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
