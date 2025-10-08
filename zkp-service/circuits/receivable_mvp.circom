pragma circom 2.1.6;

// Import Poseidon hash (ZK-friendly)
include "circomlib/circomlib.circom";
include "circomlib/poseidon.circom";

/*
ReceivableProof circuit
--------------------------------------
Proves that:
1.  There exists a private set of fields and a salt
    such that Poseidon(fields || salt) == public commitment
2.  The public disclosed values equal the corresponding
    fields inside the committed dataset
*/

template ReceivableProof(n_fields, n_public) {
    // ---------- PRIVATE INPUTS ----------
    signal input fields[n_fields];   // all hidden fields of the doc
    signal input salt;               // random salt used in commitment

    // ---------- PUBLIC INPUTS ----------
    signal input commitment;         // stored/anchored commitment
    signal input disclosed[n_public];// subset of fields to reveal (exact)

    // ---------- HASH COMMITMENT ----------
    component poseidon = Poseidon(n_fields + 1);
    for (var i = 0; i < n_fields; i++) {
        poseidon.inputs[i] <== fields[i];
    }
    poseidon.inputs[n_fields] <== salt;

    // Enforce equality: computed hash == public commitment
    poseidon.out === commitment;

    // ---------- FIELD CONSISTENCY ----------
    // For MVP, assume first n_public fields are disclosed
    for (var j = 0; j < n_public; j++) {
        fields[j] === disclosed[j];
    }

    // ---------- (OPTIONAL RULES) ----------
    // Example: total_amount_due = taxable_amount + tax_amount
    // Uncomment and adapt indices as needed:
    // fields[2] === fields[3] + fields[4];
}

component main = ReceivableProof(5, 3);
