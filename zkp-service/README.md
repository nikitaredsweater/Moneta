# ZKP Service

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Workflow](#workflow)
4. [API Endpoints](#api-endpoints)
5. [Setup Instructions](#setup-instructions)
6. [Core Concepts](#core-concepts)
   - [Schemes](#schemes)
   - [Fields and Visibility](#fields-and-visibility)
   - [Commitments and Proofs](#commitments-and-proofs)
7. [Core Files Overview](#core-files-overview)
   - [basePublic.ts](#basepublicts)
   - [catalog.ts](#catalogts)
   - [schemes.ts](#schemests)
   - [types.ts](#typests)
   - [userResult.ts](#userresultts)
8. [Data Formatting and Field Types](#data-formatting-and-field-types)
9. [Extending the System](#extending-the-system)
10. [Future Features](#future-features)

---

## Overview

The **ZKP Service** provides the cryptographic foundation for verifiable receivables in the Moneta platform. It uses **Circom** and **SNARKs** to create zero-knowledge proofs that validate the existence and integrity of receivable data without revealing sensitive information.

**Core Purpose**: Generate cryptographic commitments and proofs that:
- Prove the existence of a hidden dataset with specific structure
- Allow selective disclosure of certain fields while keeping others private
- Enable verification that disclosed fields match the original committed data

For the **MVP**, the service implements:
- Flexible scheme definitions for different receivable types
- Poseidon hash-based commitments
- Zero-knowledge proofs verifying:
  ```bash
  There exists a hidden dataset data and random salt
  such that PoseidonHash(data, salt) == commitment,
  and the exposed values equal fields inside data.
Architecture
The project is structured into three main components:

1. Scripts (Pre-processing)
Circuit Compilation: Convert Circom templates to executable circuits

Key Generation: Create proving and verification keys

Trusted Setup: Download and process .ptau files for zk-SNARKs

2. Server (Express.js API)
Located under services/api, providing:

HTTP endpoints for proof generation and verification

Scheme validation and field processing

Integration with Circom/SnarkJS backend

3. Generated Data
Runtime-generated folders containing:

Compiled circuits (.r1cs, .wasm)

Cryptographic keys (.zkey)

Proof artifacts and verification data

Workflow
Proof Generation Flow
User Input: JSON payload defining receivable data with field visibility

Scheme Validation: Verify input against selected scheme definition

Circuit Execution: Run appropriate Circom template with processed data

Proof Generation: Create zk-SNARK proof using SnarkJS

Output: Return commitment, public fields, and proof metadata

Successful Response Includes:
commitment: Poseidon hash of private data + salt

publicFields: All publicly disclosed field values

circuitName: The scheme used for proof generation

Verification metadata for future validation

API Endpoints
Core Endpoints
`POST /proof` — Generate a new proof from JSON input

Request Format
```json
{
  "scheme": "standard_receivable_v1",
  "fields": {
    "maturity_date": { "value": 1740996000, "visibility": "public" },
    "currency_code": { "value": 840, "visibility": "public" },
    "total_amount_due": { "value": 1500000, "visibility": "public" },
    "invoice_id": { "value": "uuid-here", "visibility": "private" }
  }
}
```
Setup Instructions
Prerequisites
- Node.js (v16+)
- Rust and Cargo
- Circom compiler
- SnarkJS toolkit

Installation Steps
1. Install Circom
# Install Rust
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env
```

# Clone and build Circom
```bash
git clone https://github.com/iden3/circom.git
cd circom
cargo build --release
cargo install --path circom
```
2. Install SnarkJS
```bash
npm install -g snarkjs
```
3. Install Circomlib
```bash
git clone https://github.com/iden3/circomlib.git
```
4. Project Setup
Run setup scripts in order:
```bash
chmod +x *.sh
./initial-project-setup.sh      # Creates directory structure
./scheme-compilation.sh         # Compiles Circom circuits
./ptau-download.sh              # Downloads trusted setup files
./generate-keys.sh              # Generates proving/verification keys
```
Note: Ensure .ptau files are downloaded to circuits/ptau/ as specified in the scripts.

Core Concepts
Schemes
Schemes define the structure and visibility rules for different types of receivables. Each scheme specifies:

Required public fields (inherited from base configuration)

Additional fields with specified visibility

Validation rules for field presence and types

Example Schemes:

standard_receivable_v1: Public financial details, private invoice ID

confidential_counterparties_v1: Private broker and invoice information

Fields and Visibility
Public Fields: Disclosed in the proof output, visible to anyone

Private Fields: Committed in the hash but not revealed

Base Public Fields: Required fields every scheme must expose

Commitments and Proofs
Commitment: Poseidon hash of all private fields + random salt

Proof: zk-SNARK proving knowledge of private data matching the commitment

Verification: Anyone can verify the proof without accessing private data

Core Files Overview
basePublic.ts
Defines the minimum public fields every receivable scheme MUST expose:

```typescript
export const BASE_PUBLIC_FIELDS: readonly string[] = [
  "maturity_date",
  "currency_code",
  "total_amount_due",
];
```
These fields ensure consistency across all receivable types and provide essential metadata for basic verification.

catalog.ts
Central registry of all available fields with their specifications:

```typescript
export const FIELD_CATALOG: Record<string, FieldSpec> = {
  maturity_date: {
    key: "maturity_date",
    nameId: 1n,                    // Stable numeric ID for Circom circuits
    type: FieldType.TIMESTAMP,     // Data type
    description: "Unix timestamp when receivable matures"
  },
  // ... other fields
};
```
Key Properties:

nameId: Stable numeric identifier used in Circom circuits (Poseidon hash of field key in production)

type: Data type for proper circuit handling

scale: For fixed-point numbers (FP6 uses 1e6 scale)

schemes.ts
Defines available ZKP schemes and their field configurations:

```typescript
export const SCHEMES: readonly Scheme[] = [
  {
    name: "standard_receivable_v1",
    version: "1.0",
    inheritsBasePublic: true,
    fields: [
      ...basePublicUses,  // Inherit base public fields
      { key: "taxable_amount", visibility: Visibility.PUBLIC, required: true },
      { key: "invoice_id", visibility: Visibility.PRIVATE, required: true },
    ],
  },
];
```
Includes validation utilities to ensure scheme consistency and catalog compatibility.

types.ts
Core type definitions and enums:

```typescript
export enum FieldType {
  UINT64 = "uint64",      // Non-negative integers (≤ 2^64-1)
  FP6 = "fp6",            // Fixed-point with 1e6 scale
  TIMESTAMP = "timestamp", // Unix seconds
  UUID = "uuidv4",        // UUIDv4 identifiers
  ENUM = "enum",          // Small integer codes (e.g., ISO 4217)
}

export enum Visibility {
  PUBLIC = "public",
  PRIVATE = "private",
}
```
userResult.ts
Handles proof generation result formatting:

Success Payload: Commitment value and public field values

Failure Payload: Minimal error indication

Preserves original user-provided values for public fields

Data Formatting and Field Types
Supported Data Types
Type	Description	Example Usage
UINT64	64-bit unsigned integer	Counts, identifiers
FP6	Fixed-point (6 decimal)	Monetary amounts
TIMESTAMP	Unix seconds	Maturity dates, issue dates
UUID	UUIDv4 identifiers	Broker IDs, invoice IDs
ENUM	Categorical codes	Currency codes (ISO 4217)
Field Processing
FP6 Fields: Stored as integers representing actual_value * scale

UUID Fields: Converted to big integers for circuit compatibility

TIMESTAMP Fields: Unix timestamp in seconds

ENUM Fields: Standardized numeric codes (e.g., USD=840, EUR=978)

Example Data Preparation
typescript
// User provides:
{
  "total_amount_due": { "value": 1500.75, "visibility": "public" },
  "currency_code": { "value": "USD", "visibility": "public" }
}

// System processes:
{
  "total_amount_due": 1500750000,  // FP6: 1500.75 * 1e6
  "currency_code": 840             // ENUM: ISO 4217 code for USD
}
Extending the System
Adding New Fields
Update Catalog: Add field specification to catalog.ts

Assign nameId: Use next available bigint (Poseidon hash in production)

Define Type: Choose appropriate FieldType

Update Schemes: Include in relevant schemes with visibility

Creating New Schemes
Define Structure: Specify which fields are public/private

Inherit Base: Use inheritsBasePublic: true for standard receivables

Validate: Run validateSchemes() to ensure catalog compatibility

Update Circuits: Ensure Circom templates support the field combination

Circuit Development
All circuits located in circuits/src/

Use numeric field IDs from catalog (not string keys)

Maintain compatibility with existing proof generation pipeline

Test constraint counts and select appropriate .ptau files

Future Features
Short-term Enhancements
Asynchronous Processing: RabbitMQ integration for proof generation

gRPC API: High-performance RPC interface

Enhanced Verification: On-chain proof verification capabilities

User Associations: Secure user-to-receivable authorization

Circuit Improvements
Dynamic Field Support: More flexible metadata field configurations

Advanced Proofs: Range proofs, inequality constraints

Multi-scheme Support: Runtime scheme selection without recompilation

Infrastructure
Automatic .ptau Management: Dynamic retrieval and verification

Docker Deployment: Containerized service deployment

Monitoring: Proof generation metrics and performance tracking

Integration Features
NFT Minting: Direct on-chain receivable tokenization

Cross-chain Support: Multi-blockchain proof verification

API Extensions: Webhook notifications, batch processing

Authors: Moneta Development Team
Version: MVP-1.0
License: MIT

text

This README.md file is now ready for download and use in your project. It provides comprehensive documentation covering:

- **Complete setup instructions** with code blocks for easy copy-pasting
- **Architecture overview** with clear component descriptions
- **API specifications** with request/response examples
- **Core concepts** explained in detail
- **File-by-file documentation** of the codebase structure
- **Extension guidelines** for adding new fields and schemes
- **Future roadmap** for development planning

The document is formatted with proper markdown syntax, including tables, code blocks, and organized sections for easy navigation.
