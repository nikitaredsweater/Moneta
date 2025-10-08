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
