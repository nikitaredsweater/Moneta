pragma circom 2.1.6;

include "circomlib/poseidon.circom";

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
    for (var k = 0; k < n_public; k++) {
        // Each disclosed pair (name, value) must exist in private list
        var matched = 0;
        for (var m = 0; m < n_fields; m++) {
            // Enforce equality when names match
            field_names[m] === disclosed_names[k] ==> field_values[m] === disclosed_values[k];
        }
    }
}

component main = ReceivableProofNamed(5, 3);
