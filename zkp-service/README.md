# ZKP Service

[Work in progress] This service performs the central encryption and accountability (commitment) functions of the platform. For MVP, this service aims to do the following workflow:

- Get a list of private fields that make up the contract and are important for the contract verification in the future + for selling of the receivable. These fields can be divided into `private_fields` and `public_fields`
- Use PoseidonHash to create commitment hash.
- User receives a salt needed to decode the values passed. They become accountable to keep this value private and are accountable to make it public for audits and legal purposes (if asked). Failing to do so will be fully on the sholders of the issuing company.
- Use circom template that will verify the following statement:
``` bash
    There exists a hidden dataset data and random salt
    such that PoseidonHash(data, salt) == commitment,
    and the exposed values equal fields inside data.
```
- Then the ZKP service will make the verification documents that can be attached to a solidity contract in the future.

* The scheme can also verify some addtional facts in the future *

The zkp service will also have HTTP endpoints for creation of such commitment and zkps.

The project is divided into three main parts:
1) scripts - files that need to be executed before starting the server. They are needed to turn the incomming data JSON data into the Zero-Knowledge Proofs by setting tools like circom and snarkjs; by creating encryption keys.
2) Server - ExpressJS server that lives under services/api. It is a rather simple server which has one main job - accept incomming HTTP JSON requests and form out of them the proof.json and output.json files.
3) Different data folders - these are generated when scripts are run and when the server runs. It is much easier to let the scripts to run than to figure out which folders you need. initial-project-setup.sh is present to generate folders that are ignored by .gitignore.


API ENDPOINTS:
[LET AI GENERATE]

SETUP INSTRUCTIONS:
This project is difficult to setup. It uses side projects to perform its main functions of encryption.
That includes: circom and circomlib. Also, snarkjs is installed with npm, but that is not difficult to install.

How to install circom:
Follow the guide here [https://docs.circom.io/getting-started/installation/#installing-dependencies]
Here is a summary of the steps that need to be carried (in case the documentation gets deleted):
Installing dependencies
You need several dependencies in your system to run circom and its associated tools.

The core tool is the circom compiler which is written in Rust. To have Rust available in your system, you can install rustup. If you’re using Linux or macOS, open a terminal and enter the following command:
curl --proto '=https' --tlsv1.2 https://sh.rustup.rs -sSf | sh
We also distribute a series of npm packages so Node.js and some package manager like npm or yarn should be available in your system. Recent versions of Node.js include big integer support and web assembly compilers that help run code faster, so to get a better performance, install version 10 or higher.
Installing circom
To install from our sources, clone the circom repository:

git clone https://github.com/iden3/circom.git
Enter the circom directory and use the cargo build to compile:

cargo build --release
The installation takes around 3 minutes to be completed. When the command successfully finishes, it generates the circom binary in the directory target/release. You can install this binary as follows (Note: Make sure you're still in the circom directory when running this command) :

cargo install --path circom
The previous command will install the circom binary in the directory $HOME/.cargo/bin.

Now, you should be able to see all the options of the executable by using the help flag:

circom --help

circom compiler 2.2.2
IDEN3
Compiler for the circom programming language

USAGE:
    circom [FLAGS] [OPTIONS] [--] [input]

FLAGS:
        --r1cs                                 Outputs the constraints in r1cs format
        --sym                                  Outputs witness in sym format
        --wasm                                 Compiles the circuit to wasm
        --json                                 Outputs the constraints in json format
        --wat                                  Compiles the circuit to wat
    -c, --c                                    Compiles the circuit to C++
        --O0                                   No simplification is applied
        --O1                                   Only applies signal to signal and signal to constant simplification. This
                                               is the default option
        --O2                                   Full constraint simplification
        --verbose                              Shows logs during compilation
        --inspect                              Does an additional check over the constraints produced
        --constraint_assert_dissabled          Does not add asserts in the witness generation code to check constraints
                                               introduced with "==="
        --use_old_simplification_heuristics    Applies the old version of the heuristics when performing linear
                                               simplification
        --simplification_substitution          Outputs the substitution applied in the simplification phase in json
                                               format
        --no_asm                               Does not use asm files in witness generation code in C++
        --no_init                              Removes initializations to 0 of variables ("var") in the witness
                                               generation code
    -h, --help                                 Prints help information
    -V, --version                              Prints version information

OPTIONS:
    -o, --output <output>                    Path to the directory where the output will be written [default: .]
    -p, --prime <prime>                      To choose the prime number to use to generate the circuit. Receives the
                                             name of the curve (bn128, bls12377, bls12381, goldilocks, grumpkin, pallas,
                                             secq256r1, vesta) [default: bn128]
    -l <link_libraries>...                   Adds directory to library search path
        --O2round <simplification_rounds>    Maximum number of rounds of the simplification process

ARGS:
    <input>    Path to a circuit with a main component [default: ./circuit.circom]
Installing snarkjs
snarkjs is a npm package that contains code to generate and validate ZK proofs from the artifacts produced by circom.

You can install snarkjs with the following command:

npm install -g snarkjs

Installing circomlib:
Install with: git clone https://github.com/iden3/circomlib.git

Then run all of the bash files in order:
1) initial-project-setup.sh
2) scheme-compilation.sh
3) ptau-download.sh
4) generate-keys.sh

do not forget to chmod +x all of these files [ai, give the command]

Refer to the step with the creation of new circom templates to learn what tweeks to make to ptau-download.sh. It is currently only setted up for the MVP


Creating new schemes and templates in the future:
Right now, for MVP, there exists a single .circom template, found in under circuits/src. Put all of the new circuit templates there when you make them.

Current template, in reality, is relatively flexible. It allows any number of inputs for the receivable metadata to be entered, but when you compile you must have a fixed number of paramters. Currently - 6 in total and 5 of them are public.

Likely, in the future this can be updated.

An advice: circom and circomlib both have a vast collection of exmpale templates. Look at them before making your own.

Each circuit uses different number of constraints. You need to ensure that there is an appropriate ptau file downloaded when you run the bash scripts. To learn which ptau you need, refer to this:
# After successfully running the scheme-compilation.sh file, you need to make
# sure that you have all necessary .ptau files for each of your schemes.
#
# For that, you need to find out how many constraints a scheme has
# To do that, you can run:
#
# npm snarkjs r1cs info [scheme_name].r1cs
#
#
# Then, go to:
#
# https://github.com/iden3/snarkjs?tab=readme-ov-file#7-prepare-phase-2
#
# and select the correct ptau file to download. Name it hez[n].ptau, where n is
# the power.
#
#
# Download the files into circuits/ptau/ folder. It is marked to be
# ignored by git.
#
# Example instruction to copy the file:
#
# wget https://storage.googleapis.com/zkevm/ptau/powersOfTau28_hez_final_08.ptau -O hez8.ptau
#
#
# Maybe later I will implement a script that will do this automatically, but not right now
#
# Guides:
#   - https://habr.com/ru/companies/metalamp/articles/869414/
#   - https://github.com/iden3/snarkjs?tab=readme-ov-file#7-prepare-phase-2


This System is designed to allow users to create ZK Proofs simply through a JSON. There is some formatting that was done to allow that. We use schemes to define which fields we expect to make a ZKP. Each scheme is made out of public fields (that will be visible when receivable is minted), and private fields (that are stored in the commitment hash but which are not revieled ever). Each scheme has a set of required public fields. Each field also has a couple of variables associated with them, including type, name, and id. Since the circom templates do not allow to use strings, we use int-based ids to represent all possible fields that can be assigned to a receivable NFT. It does mean that the mapping of the int-based ids and the names must be piblicly availbale in a db, but currently this feature is not implemented.

Here is a full list of defined schemes:
[AI]

Here is a full list of the supported field types:
[AI]

Here is a full list of the supported field names and their id mapping:
[AI]


If all checks pass, the user who asked to make this proof will receive a confirmation that it was made, as well as metadata: disclosed fields and their values and the commitment value. That commitment value must be stored by the owner, which will be needed to disclose the private fields in certain cases.


Future features:
when the proof was generated, we have all of the components to actually make an NFT or just to push that verification on-chain. In future, this service will also be connected to rabbitMQ and/or gRPC to send requests to do the on-chain work to the on-chain commumication service.

At this moment there is no association between the user making the request and the receivable - i.e. anyone can make these. We will be attaching the security aspect soon.

Current circuit is too small even for MVP. It will have much more fields added soon.
