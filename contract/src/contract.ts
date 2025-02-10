// Find all our documentation at https://docs.near.org
import { NearBindgen, near, call, view } from 'near-sdk-js';

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

  @view({})
  get_agreements(): string {
    return JSON.stringify(this.agreements); // Proper serialization
  }

  @call({})
  set_agreement({ agreement }: { agreement: Agreement }): void {
    near.log(`Saving agreement: ${JSON.stringify(agreement)}`);
    this.agreements.push(agreement); // Correctly pushing the new agreement
  }

  @call({})
  paySecurityDeposit({ agreementId }: { agreementId: string }): void {
    const agreement = this.agreements.find((a) => a.id === agreementId);
    if (!agreement) {
      throw new Error("Agreement not found.");
    }

    const depositAmount = BigInt(agreement.securityDeposit); // Convert to BigInt
    const attachedDeposit = near.attachedDeposit();

    if (attachedDeposit !== depositAmount) {
      throw new Error("Incorrect deposit amount.");
    }

    near.log(`Security deposit of ${depositAmount} yoctoNEAR paid for agreement ${agreementId}`);
  }

  @call({})
  payRent({ agreementId }: { agreementId: string }): void {
    const agreement = this.agreements.find((a) => a.id === agreementId);
    if (!agreement || agreement.status !== "Active") {
      throw new Error("Agreement is not active.");
    }

    const rentAmount = BigInt(agreement.monthlyRent); // Convert to BigInt
    const attachedDeposit = near.attachedDeposit(); // Get attached NEAR deposit

    if (attachedDeposit !== rentAmount) {
      throw new Error("Incorrect rent amount.");
    }

    // Transfer rent to landlord
    const promise = near.promiseBatchCreate(agreement.landlordId);
    near.promiseBatchActionTransfer(promise, rentAmount);

    near.log(`Rent of ${rentAmount} yoctoNEAR paid to ${agreement.landlordId} for agreement ${agreementId}`);
  }

  @call({})
  terminateAgreement({ agreementId }: { agreementId: string }): void {
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

  @call({})
  refundDeposit({ agreementId }: { agreementId: string }): void {
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

    const depositAmount = BigInt(agreement.securityDeposit);

    // Transfer deposit back to tenant
    const promise = near.promiseBatchCreate(agreement.tenantId);
    near.promiseBatchActionTransfer(promise, depositAmount);

    near.log(`Refunded security deposit of ${depositAmount} yoctoNEAR to ${agreement.tenantId}`);
  }

}
