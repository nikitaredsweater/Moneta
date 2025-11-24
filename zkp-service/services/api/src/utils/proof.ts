import { access, writeFile, readFile } from "fs/promises";
import { constants } from "fs";
import { join, dirname, resolve } from "path";
// @ts-ignore - snarkjs may not have perfect TypeScript definitions
import * as snarkjs from "snarkjs";

/**
 * Get the zkp-service root directory from the current file location
 */
function getZkpServiceRoot(): string {
  return join(__dirname, "..", "..", "..", "..");
}

/**
 * Resolve a path relative to zkp-service root if it's not absolute
 */
function resolveFromRoot(pathStr: string): string {
  if (resolve(pathStr) === pathStr) {
    return pathStr;
  }
  return join(getZkpServiceRoot(), pathStr);
}

export interface ProofGenerationConfig {
  /** Name of the circuit (used to locate the .zkey file) */
  circuitName: string;
  /** Path to the witness file (.wtns) */
  witnessPath?: string;
  /** Path to the proving key (.zkey) */
  zkeyPath?: string;
  /** Path to write the proof.json file */
  proofOutputPath?: string;
  /** Path to write the public.json file */
  publicOutputPath?: string;
  /** Directory containing the keys (default: "keys") */
  keysDir?: string;
}

export interface ProofGenerationResult {
  success: boolean;
  proofPath: string;
  publicPath: string;
  circuitName: string;
  executionTime: number;
  proof?: any;
  publicSignals?: any;
  error?: string;
}

/**
 * Generate a Groth16 proof using snarkjs
 * Equivalent to: snarkjs groth16 prove <zkey> <witness> <proof> <public>
 *
 * @param config - Configuration for proof generation
 * @returns Result object with success status and paths
 */
export async function generateGroth16Proof(
  config: ProofGenerationConfig
): Promise<ProofGenerationResult> {
  const startTime = Date.now();

  const {
    circuitName,
    witnessPath = resolveFromRoot("data/witness.wtns"),
    zkeyPath = config.zkeyPath ||
      resolveFromRoot(`keys/${circuitName}_final.zkey`),
    proofOutputPath = resolveFromRoot("data/proof.json"),
    publicOutputPath = resolveFromRoot("data/public.json"),
    keysDir = "keys",
  } = config;

  // Resolve all paths
  const resolvedWitnessPath = resolveFromRoot(witnessPath);
  const resolvedZkeyPath = resolveFromRoot(zkeyPath);
  const resolvedProofPath = resolveFromRoot(proofOutputPath);
  const resolvedPublicPath = resolveFromRoot(publicOutputPath);

  try {
    // Verify required files exist
    try {
      await access(resolvedWitnessPath, constants.R_OK);
    } catch {
      throw new Error(`Witness file not found: ${resolvedWitnessPath}`);
    }

    try {
      await access(resolvedZkeyPath, constants.R_OK);
    } catch {
      throw new Error(`Proving key not found: ${resolvedZkeyPath}`);
    }

    // Generate the proof using snarkjs
    const { proof, publicSignals } = await snarkjs.groth16.prove(
      resolvedZkeyPath,
      resolvedWitnessPath
    );

    // Write proof to file
    await writeFile(resolvedProofPath, JSON.stringify(proof, null, 2), "utf-8");

    // Write public signals to file
    await writeFile(
      resolvedPublicPath,
      JSON.stringify(publicSignals, null, 2),
      "utf-8"
    );

    const executionTime = Date.now() - startTime;

    return {
      success: true,
      proofPath: resolvedProofPath,
      publicPath: resolvedPublicPath,
      circuitName,
      executionTime,
      proof,
      publicSignals,
    };
  } catch (error) {
    const executionTime = Date.now() - startTime;

    if (error instanceof Error) {
      return {
        success: false,
        proofPath: resolvedProofPath,
        publicPath: resolvedPublicPath,
        circuitName,
        executionTime,
        error: error.message,
      };
    }

    return {
      success: false,
      proofPath: resolvedProofPath,
      publicPath: resolvedPublicPath,
      circuitName,
      executionTime,
      error: "Unknown error during proof generation",
    };
  }
}
