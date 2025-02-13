// Find all our documentation at https://docs.near.org
import { NearBindgen, near, call, view, initialize, UnorderedMap, assert } from 'near-sdk-js';

interface Agreement {
  id: string;
  propertyId: string;
  roomId: string;
  tenantId: string;
  landlordId: string;
  startDate: string;
  endDate: string;
  monthlyRent: string; // Stored as string to handle BigInt
  paymentDueDate: string;
  status: string;
  securityDeposit: string; // Stored as string to handle BigInt
}

@NearBindgen({})
class RentAgreement {
  agreements: Agreement[] = []; // Initialize the array
  landlord_id: string = "";
  payments = new UnorderedMap<bigint>('uid-1');
  rent_deposits = new UnorderedMap<bigint>('uid-1');

  static schema = {
    landlord_id: "string",
    payments: { class: UnorderedMap, value: "bigint" },
    rent_deposits: { class: UnorderedMap, value: "bigint" }
  }

  @initialize({ privateFunction: true })
  init({ landlord_id }: { landlord_id: string }) {
    this.landlord_id = landlord_id
  }
  
  @view({})
  get_agreements(): string {
    return JSON.stringify(this.agreements); // Proper serialization
  }

  @call({})
  set_agreement({ agreement }: { agreement: Agreement }): void {
    near.log(`Saving agreement: ${JSON.stringify(agreement)}`);
    this.agreements.push(agreement); // Correctly pushing the new agreement
  }

  @call ({ payableFunction: true })
  pay_security_deposit({ agreementId }: { agreementId: string }): void {
    const agreement = this.agreements.find((a) => a.id === agreementId);
    if (!agreement) {
      throw new Error("Agreement not found.");
    }

    const amount = BigInt(agreement.securityDeposit); // Convert to BigInt

    let tenant_id = near.predecessorAccountId();
    let depositAmount: bigint = near.attachedDeposit() as bigint;

    let total_deposits = this.rent_deposits.get(tenant_id, { defaultValue: BigInt(0) })
    let toTransfer = depositAmount;

    if (total_deposits == BigInt(0)) {
      assert(depositAmount > amount, `Attach at least ${amount} yoctoNEAR`);

      // Subtract the storage cost to the amount to transfer
      toTransfer -= amount
    }

    total_deposits += depositAmount
    this.rent_deposits.set(tenant_id, total_deposits)

    near.log(`Security deposit of ${depositAmount} yoctoNEAR paid for agreement ${agreementId}. total deposits add up to ${total_deposits}`);

    const promise = near.promiseBatchCreate(this.landlord_id)
    near.promiseBatchActionTransfer(promise, toTransfer)

    // return total_deposits.toString()
  }

  @call({ payableFunction: true })
  pay_rent({ agreementId }: { agreementId: string }): void {
    const agreement = this.agreements.find((a) => a.id === agreementId);
    if (!agreement || agreement.status !== "Active") {
      throw new Error("Agreement is not active.");
    }

    const rentAmount = BigInt(agreement.monthlyRent); // Convert to BigInt
    
    let tenant_id = near.predecessorAccountId();
    let payAmount: bigint = near.attachedDeposit() as bigint;

    let total_payments = this.payments.get(tenant_id, { defaultValue: BigInt(0) })
    let toTransfer = payAmount;

    if (total_payments == BigInt(0)) {
      assert(payAmount > rentAmount, `Attach at least ${rentAmount} yoctoNEAR`);

      // Subtract the storage cost to the amount to transfer
      toTransfer -= rentAmount
    }

    total_payments += payAmount
    this.payments.set(tenant_id, total_payments)
    
    near.log(`Rent of ${payAmount} yoctoNEAR paid to ${agreement.landlordId} for agreement ${agreementId}`);

     const promise = near.promiseBatchCreate(this.landlord_id)
    near.promiseBatchActionTransfer(promise, toTransfer)

  }

  @call({})
  terminate_agreement({ agreementId }: { agreementId: string }): void {
    const index = this.agreements.findIndex((a) => a.id === agreementId);
    if (index === -1) {
      throw new Error("Agreement not found.");
    }

    const agreement = this.agreements[index];

    if (near.signerAccountId() !== agreement.landlordId) {
      throw new Error("Only the landlord can terminate.");
    }

    agreement.status = "Terminated";
    this.agreements[index] = agreement; // Update the array correctly

    near.log(`Agreement ${agreementId} has been terminated.`);
  }

  @call({ payableFunction: true })
  refund_deposit({ agreementId }: { agreementId: string }): void {
    const agreement = this.agreements.find((a) => a.id === agreementId);
    if (!agreement) {
      throw new Error("Agreement not found.");
    }

    if (agreement.status !== "Completed" && agreement.status !== "Terminated") {
      throw new Error("Agreement must be completed or terminated.");
    }

    if (near.signerAccountId() !== agreement.landlordId) {
      throw new Error("Only the landlord can approve refunds.");
    }

  const amount = BigInt(agreement.securityDeposit); // Convert to BigInt

    let landlord_id = near.predecessorAccountId();
    let depositAmount: bigint = near.attachedDeposit() as bigint;

    let total_deposits = this.rent_deposits.get(agreement.tenantId, { defaultValue: BigInt(0) })
    let toTransfer = depositAmount;

    if (total_deposits == BigInt(0)) {
      assert(depositAmount > amount, `Attach at least ${amount} yoctoNEAR`);

      // Subtract the storage cost to the amount to transfer
      toTransfer -= amount
    }

    total_deposits += depositAmount
    this.rent_deposits.set(landlord_id, total_deposits)


    near.log(`Refunded security deposit of ${depositAmount} yoctoNEAR to ${agreement.tenantId}`);
      const promise = near.promiseBatchCreate(agreement.tenantId)
    near.promiseBatchActionTransfer(promise, toTransfer)
  }

}
