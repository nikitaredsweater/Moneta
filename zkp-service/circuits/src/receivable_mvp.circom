pragma circom 2.1.6;

// Note: This requires circomlib to be installed
// Install with: git clone https://github.com/iden3/circomlib.git
// Compile with: circom receivable_mvp.circom --r1cs --wasm --sym -l ./circomlib/circuits

include "poseidon.circom";
include "comparators.circom";

/*
ReceivableProofNamed
------------------------------------------
Proves that:
1.  There exists a private list of (name, value) pairs and a salt
    such that Poseidon( hash(name_i, value_i) for all i , salt ) == public commitment
2.  The public disclosed values equal the corresponding named fields
*/

template ReceivableProofNamed(n_fields, n_public) {
    // ---------- PRIVATE INPUTS ----------
    signal input field_names[n_fields];   // numerical IDs or hashed names
    signal input field_values[n_fields];  // hidden values
    signal input salt;                    // random salt

    // ---------- PUBLIC INPUTS ----------
    signal input commitment;              // Poseidon root (public)
    signal input disclosed_names[n_public];
    signal input disclosed_values[n_public];

    // ---------- HASH EACH FIELD (name,value) ----------
    component field_hash[n_fields];
    for (var i = 0; i < n_fields; i++) {
        field_hash[i] = Poseidon(2);
        field_hash[i].inputs[0] <== field_names[i];
        field_hash[i].inputs[1] <== field_values[i];
    }

    // ---------- HASH ALL FIELD HASHES + SALT ----------
    component total_hash = Poseidon(n_fields + 1);
    for (var j = 0; j < n_fields; j++) {
        total_hash.inputs[j] <== field_hash[j].out;
    }
    total_hash.inputs[n_fields] <== salt;

    // Enforce that computed hash equals the public commitment
    total_hash.out === commitment;

    // ---------- CONSISTENCY FOR DISCLOSED FIELDS ----------
    component name_eq[n_public][n_fields];
    signal matched_values[n_public][n_fields];
    signal accumulator[n_public][n_fields];
    signal sum_matched[n_public];  // Declare outside the loop

    for (var k = 0; k < n_public; k++) {
        for (var m = 0; m < n_fields; m++) {
            // Check if names match
            name_eq[k][m] = IsEqual();
            name_eq[k][m].in[0] <== field_names[m];
            name_eq[k][m].in[1] <== disclosed_names[k];

            // If names match, the values should match
            // matched_values = name_eq * (field_values[m] - disclosed_values[k])
            matched_values[k][m] <== name_eq[k][m].out * (field_values[m] - disclosed_values[k]);

            // Accumulate to ensure at least one match exists
            if (m == 0) {
                accumulator[k][m] <== name_eq[k][m].out;
            } else {
                accumulator[k][m] <== accumulator[k][m-1] + name_eq[k][m].out;
            }
        }

        // Ensure the values match when names match (must be 0)
        sum_matched[k] <== matched_values[k][0] + matched_values[k][1] + matched_values[k][2] + matched_values[k][3] + matched_values[k][4];
        sum_matched[k] === 0;

        // Ensure at least one name matched (accumulator should be >= 1)
        // This constraint ensures the disclosed name exists in the private list
        accumulator[k][n_fields-1] * (accumulator[k][n_fields-1] - 1) === 0;
        accumulator[k][n_fields-1] === 1;
    }
}

component main {public [commitment, disclosed_names, disclosed_values]} = ReceivableProofNamed(6, 5);
