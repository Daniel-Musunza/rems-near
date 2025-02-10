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
}
