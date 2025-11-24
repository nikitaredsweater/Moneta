import { Scheme, Visibility } from "../receivable";

type FieldsInput = Record<string, { value: unknown; visibility: unknown }>;


export type SuccessPayload = {
  success: true;
  circuitName: string;
  commitment:string;
  publicFields: Record<string, unknown>;
};

export type FailurePayload = {
  success: false;
};


/**
 * Build minimal success payload for the user: all public fields, original values.
 * Pass the same `scheme` you validated against and the original `body.fields`.
 */
export function buildSuccessUserPayload(
  scheme: Scheme,
  bodyFields: FieldsInput,
  commitment: string
): SuccessPayload {
  const publicFields: Record<string, unknown> = {};

  for (const f of scheme.fields) {
    if (f.visibility === Visibility.PUBLIC) {
      const provided = bodyFields[f.key];
      if (provided) {
        // Return the original human-readable value the user sent
        publicFields[f.key] = provided.value;
      }
    }
  }

  return {
    success: true,
    circuitName: scheme.name,
    commitment,
    publicFields,
  };
}

/** Minimal failure payload: no reason included */
export function buildFailureUserPayload(): FailurePayload {
  return { success: false };
}
