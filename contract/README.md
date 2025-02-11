# REM NEAR Contract

The smart contract exposes two methods to enable storing and retrieving a greeting in the NEAR network.

```ts
@NearBindgen({})
class RentAgreement {
  agreements: Agreement[] = []; // Initialize the array

  @view({})
  get_agreements(): string {
    return JSON.stringify(this.agreements); // Proper serialization
  }

  @call({})
  set_agreement({ agreement }: { agreement: Agreement }): void {
    near.log(`Saving agreement: ${JSON.stringify(agreement)}`);
    this.agreements.push(agreement); // Correctly pushing the new agreement
  }
}
```

<br />

# Quickstart

1. Make sure you have installed [node.js](https://nodejs.org/en/download/package-manager/) >= 16.
2. Install the [`NEAR CLI`](https://github.com/near/near-cli#setup)

<br />

## 1. Build and Test the Contract
You can automatically compile and test the contract by running:

```bash
npm run build
```

<br />

## 2. Create an Account and Deploy the Contract
You can create a new account and deploy the contract by running:

```bash
near create-account threecommas.testnet --useFaucet
near deploy threecommas.testnet build/rems-near.wasm
```

<br />


## 3. Retrieve the agreements

`get_agreements` is a read-only method (aka `view` method).

`View` methods can be called for **free** by anyone, even people **without a NEAR account**!

```bash
# Use near-cli to get the agreements
near view threecommas.testnet get_agreements
```

<br />

## 4. Store a New agreement
`set_agreement` changes the contract's state, for which it is a `call` method.

`Call` methods can only be invoked using a NEAR account, since the account needs to pay GAS for the transaction.

```bash
# Use near-cli to set a new greeting
near call threecommas.testnet set_agreement '{"agreement":{
  "id": "1",
  "propertyId": "A400",
  "roomId": "1D",
  "tenantId": "MH03",
  "landlordId": "23OI",
  "startDate": "03/07/2024",
  "endDate": "",
  "monthlyRent": "12000",
  "paymentDueDate": "5",
  "status": "Active",
  "securityDeposit": "29000"
}}' --accountId threecommas.testnet

```

**Tip:** If you would like to call `set_agreement` using another account, first login into NEAR using:

```bash
# Use near-cli to login your NEAR account
near login
```

and then use the logged account to sign the transaction: `--accountId threecommas.testnet`