import fs from "fs/promises";
import { encodeValue, FIELD_CATALOG } from "../receivable";
import { computePoseidonCommitmentSeparate, generateSalt } from "./commitment";
import { exec } from "child_process";
import { promisify } from "util";
import path from "path";

const execAsync = promisify(exec);

export interface WitnessGenerationConfig {
  /** Name of the circuit (e.g., "ReceivableProofNamed") */
  circuitName: string;
  /** Path to the compiled circuit directory (default: "./circuits") */
  circuitsDir?: string;
  /** Path to input.json (default: "./input.json") */
  inputJsonPath?: string;
  /** Output path for witness file (default: "./witness.wtns") */
  outputWitnessPath?: string;
}

export interface WitnessGenerationResult {
  success: boolean;
  witnessPath: string;
  circuitName: string;
  executionTime: number;
  error?: string;
  stdout?: string;
  stderr?: string;
}

/**
 * Prepare input.json for the Circom circuit from an HTTP request body
 *
 * @param requestBody - The body from POST /receivable/create
 * @param schemeName - Name of the scheme (e.g., "standard_receivable_v1")
 * @param outputPath - Path where to write input.json (optional)
 * @returns The circuit input object
 */
export async function prepareCircuitInput(
  requestBody: {
    scheme?: string;
    fields?: Record<
      string,
      { value: unknown; visibility: "public" | "private" }
    >;
  },
  outputPath?: string
) {
  if (!requestBody.fields || typeof requestBody.fields !== "object") {
    throw new Error("Invalid request body: fields required");
  }

  // Extract all fields with their metadata
  const allFields: Array<{
    key: string;
    nameId: bigint;
    value: bigint;
    visibility: "public" | "private";
  }> = [];

  for (const [key, fieldData] of Object.entries(requestBody.fields)) {
    const spec = FIELD_CATALOG[key];
    if (!spec) {
      throw new Error(`Unknown field: ${key}`);
    }

    const encodedValue = encodeValue(spec, fieldData.value);
    allFields.push({
      key,
      nameId: spec.nameId,
      value: encodedValue,
      visibility: fieldData.visibility,
    });
  }

  // Generate salt
  const salt = generateSalt();

  // Compute commitment (matching circuit structure)
  const commitment = await computePoseidonCommitmentSeparate(
    allFields.map((f) => ({ nameId: f.nameId, value: f.value })),
    salt
  );

  // Separate public and private fields
  const publicFields = allFields.filter((f) => f.visibility === "public");
  const privateFields = allFields; // Circuit needs all fields as private inputs

  // Prepare circuit input
  const circuitInput = {
    // Private inputs
    field_names: privateFields.map((f) => f.nameId.toString()),
    field_values: privateFields.map((f) => f.value.toString()),
    salt: salt.toString(),

    // Public inputs
    commitment: commitment.toString(),
    disclosed_names: publicFields.map((f) => f.nameId.toString()),
    disclosed_values: publicFields.map((f) => f.value.toString()),
  };

  // Optionally write to file
  if (outputPath) {
    await fs.writeFile(
      outputPath,
      JSON.stringify(circuitInput, null, 2),
      "utf-8"
    );
    console.log(`Circuit input written to ${outputPath}`);
  }

  return {
    circuitInput,
    commitment: commitment.toString(),
    salt: salt.toString(),
    metadata: {
      totalFields: allFields.length,
      publicFields: publicFields.length,
      fieldKeys: allFields.map((f) => f.key),
    },
  };
}

/**
 * Generate a witness file (.wtns) from input.json using the compiled circuit
 *
 * @param config - Configuration for witness generation
 * @returns Result object with success status and paths
 */
export async function generateWitness(
  config: WitnessGenerationConfig
): Promise<WitnessGenerationResult> {
  const startTime = Date.now();

  const {
    circuitName,
    circuitsDir = config.circuitsDir ? config.circuitsDir : "./circuits",
    inputJsonPath = config.inputJsonPath
      ? config.inputJsonPath
      : "./input.json",
    outputWitnessPath = config.outputWitnessPath
      ? config.outputWitnessPath
      : "./witness.wtns",
  } = config;

  console.log(config)

  // Construct paths
  const jsDir = path.join(circuitsDir, `${circuitName}_js`);
  const wasmPath = path.join(jsDir, `${circuitName}.wasm`);
  const generateWitnessScript = path.join(jsDir, "generate_witness.js");

  console.log(jsDir, "\n", wasmPath, "\n", generateWitnessScript);

  try {
    // Verify files exist
    await fs.access(generateWitnessScript);
    await fs.access(wasmPath);
    await fs.access(inputJsonPath);

    // Build the command
    const command = `node "${generateWitnessScript}" "${wasmPath}" "${inputJsonPath}" "${outputWitnessPath}"`;

    console.log(`Generating witness for circuit: ${circuitName}`);
    console.log(`Command: ${command}`);

    // Execute the command
    const { stdout, stderr } = await execAsync(command, {
      maxBuffer: 10 * 1024 * 1024, // 10MB buffer for large circuits
    });

    // Verify witness file was created
    await fs.access(outputWitnessPath);

    const executionTime = Date.now() - startTime;

    return {
      success: true,
      witnessPath: outputWitnessPath,
      circuitName,
      executionTime,
      stdout: stdout.trim(),
      stderr: stderr.trim(),
    };
  } catch (error) {
    const executionTime = Date.now() - startTime;

    if (error instanceof Error) {
      // Check for specific error types
      if (error.message.includes("ENOENT")) {
        return {
          success: false,
          witnessPath: outputWitnessPath,
          circuitName,
          executionTime,
          error:
            `Required files not found. Ensure circuit is compiled and paths are correct:\n` +
            `  - ${generateWitnessScript}\n` +
            `  - ${wasmPath}\n` +
            `  - ${inputJsonPath}`,
        };
      }

      return {
        success: false,
        witnessPath: outputWitnessPath,
        circuitName,
        executionTime,
        error: error.message,
        stderr: (error as any).stderr,
        stdout: (error as any).stdout,
      };
    }

    return {
      success: false,
      witnessPath: outputWitnessPath,
      circuitName,
      executionTime,
      error: "Unknown error during witness generation",
    };
  }
}

/**
 * Generate witness with customizable paths based on circuit name
 *
 * @param circuitName - Name of the circuit
 * @param inputJsonPath - Optional path to input.json (default: "./input.json")
 * @param circuitsDir - Optional path to circuits directory (default: "./circuits")
 * @param outputWitnessPath - Optional path for output witness file (default: "./witness.wtns")
 * @returns Result object
 */
export async function generateWitnessSimple(
  config: WitnessGenerationConfig
): Promise<WitnessGenerationResult> {
  return generateWitness(config);
}

/**
 * Batch witness generation for multiple circuits
 *
 * @param configs - Array of witness generation configs
 * @returns Array of results
 */
export async function generateWitnessBatch(
  configs: WitnessGenerationConfig[]
): Promise<WitnessGenerationResult[]> {
  const results: WitnessGenerationResult[] = [];

  for (const config of configs) {
    const result = await generateWitness(config);
    results.push(result);

    if (!result.success) {
      console.error(`Failed to generate witness for ${config.circuitName}`);
      console.error(result.error);
    }
  }

  return results;
}
