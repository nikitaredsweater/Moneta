import { encodeValue, FIELD_CATALOG } from "../receivable";
import { computePoseidonCommitmentSeparate, generateSalt } from "./commitment";
import { exec } from "child_process";
import { promisify } from "util";
import { access, mkdir, writeFile } from "fs/promises";
import { constants } from "fs";
import { join, dirname, resolve } from "path";

const execAsync = promisify(exec);

export interface WitnessGenerationConfig {
  circuitName: string;
  circuitsDir?: string;
  inputJsonPath?: string;
  outputWitnessPath?: string;
}

export interface WitnessGenerationResult {
  success: boolean;
  witnessPath: string;
  circuitName: string;
}

/**
 * Get the zkp-service root directory from the current file location
 * Current file: zkp-service/services/api/src/utils/witness.ts
 * Root: zkp-service/
 */
function getZkpServiceRoot(): string {
  // Go up 4 levels: utils -> src -> api -> services -> zkp-service
  return join(__dirname, "..", "..", "..", "..");
}

/**
 * Get the default circuits directory path
 * Returns: zkp-service/circuits
 */
function getDefaultCircuitsDir(): string {
  return join(getZkpServiceRoot(), "circuits", "src");
}

/**
 * Resolve a path relative to zkp-service root if it's not absolute
 */
function resolveFromRoot(pathStr: string): string {
  if (resolve(pathStr) === pathStr) {
    // Already absolute
    return pathStr;
  }
  // Relative path - resolve from zkp-service root
  return join(getZkpServiceRoot(), pathStr);
}

/**
 * Prepare input.json for the Circom circuit from an HTTP request body
 *
 * @param requestBody - The body from POST /receivable/create
 * @param schemeName - Name of the scheme (e.g., "standard_receivable_v1")
 * @param outputPath - Path where to write input.json (relative to zkp-service root or absolute)
 *                     Default: "inputs/input.json" (relative to zkp-service root)
 * @returns The circuit input object with commitment and metadata
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
  // Validate input
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

  // Write to file if path is provided
  if (outputPath) {
    // Resolve path relative to zkp-service root
    const resolvedOutputPath = resolveFromRoot(outputPath);

    console.log(`Preparing to write circuit input to: ${resolvedOutputPath}`);

    try {
      // Ensure the directory exists
      const dir = dirname(resolvedOutputPath);
      await mkdir(dir, { recursive: true });
      console.log(`✓ Directory ensured: ${dir}`);

      // Write the file
      await writeFile(
        resolvedOutputPath,
        JSON.stringify(circuitInput, null, 2),
        "utf-8"
      );
      console.log(
        `✅ Circuit input written successfully to: ${resolvedOutputPath}`
      );
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      throw new Error(
        `Failed to write circuit input to ${resolvedOutputPath}: ${errorMsg}`
      );
    }
  } else {
    // Default path if none provided
    const defaultPath = resolveFromRoot("inputs/input.json");

    console.log(`No output path specified, using default: ${defaultPath}`);

    try {
      const dir = dirname(defaultPath);
      await mkdir(dir, { recursive: true });

      await writeFile(
        defaultPath,
        JSON.stringify(circuitInput, null, 2),
        "utf-8"
      );
      console.log(
        `✅ Circuit input written to default location: ${defaultPath}`
      );
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : "Unknown error";
      throw new Error(
        `Failed to write circuit input to ${defaultPath}: ${errorMsg}`
      );
    }
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
  // FIXME: FOR MVP these vlaues are more-less hardcoded, this needs
  // to be fixed.
  const {
    circuitName,
    circuitsDir = getDefaultCircuitsDir(),
    inputJsonPath = resolveFromRoot("data/input/input.json"),
    outputWitnessPath = resolveFromRoot("data/output/witness.wtns"),
  } = config;

  // Resolve circuitsDir from root if relative
  const resolvedCircuitsDir = resolveFromRoot(circuitsDir);

  // Construct paths to compiled circuit files
  const jsDir = join(resolvedCircuitsDir, `${circuitName}_js`);
  const wasmPath = join(jsDir, `${circuitName}.wasm`);
  const generateWitnessScript = join(jsDir, "generate_witness.js");

  try {
    // Verify files exist
    try {
      await access(generateWitnessScript, constants.R_OK);
    } catch {
      throw new Error(
        `generate_witness.js not found at: ${generateWitnessScript}`
      );
    }

    try {
      await access(wasmPath, constants.R_OK);
    } catch {
      throw new Error(`WASM file not found at: ${wasmPath}`);
    }

    try {
      await access(inputJsonPath, constants.R_OK);
    } catch {
      throw new Error(`input.json not found at: ${inputJsonPath}`);
    }

    // Build the command
    const command = `node "${generateWitnessScript}" "${wasmPath}" "${inputJsonPath}" "${outputWitnessPath}"`;

    // Execute the command
    const { stdout, stderr } = await execAsync(command, {
      maxBuffer: 10 * 1024 * 1024, // 10MB buffer for large circuits
    });

    // Verify witness file was created
    await access(outputWitnessPath, constants.R_OK);

    return {
      success: true,
      witnessPath: outputWitnessPath,
      circuitName,
    };
  } catch (error) {

    if (error instanceof Error) {
      console.error(error.message);

      // Check for specific error types
      if (
        error.message.includes("ENOENT") ||
        error.message.includes("not found")
      ) {
        return {
          success: false,
          witnessPath: outputWitnessPath,
          circuitName,
        };
      }

      return {
        success: false,
        witnessPath: outputWitnessPath,
        circuitName,
      };
    }

    return {
      success: false,
      witnessPath: outputWitnessPath,
      circuitName,
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
  }

  return results;
}
