// import { NearBindgen, near, call, view } from 'near-sdk-js';

// interface Agreement {
//     id: string;
//     propertyId: string;
//     roomId: string;
//     tenantId: string;
//     landlordId: string;
//     startDate: string;
//     endDate: string;
//     monthlyRent: bigint;
//     paymentDueDate: string;
//     status: string;
//     securityDeposit: bigint;
// }

// @NearBindgen({})
// class RentAgreement implements Agreement {
//     id: string;
//     propertyId: string;
//     roomId: string;
//     tenantId: string;
//     landlordId: string;
//     startDate: string;
//     endDate: string;
//     monthlyRent: bigint;
//     paymentDueDate: string;
//     status: string;
//     securityDeposit: bigint;

//     constructor(id: string, propertyId: string, roomId: string, tenantId: string, landlordId: string, startDate: string, endDate: string, monthlyRent: bigint, paymentDueDate: string, securityDeposit: bigint) {
//         this.id = id;
//         this.propertyId = propertyId;
//         this.roomId = roomId;
//         this.tenantId = tenantId;
//         this.landlordId = landlordId;
//         this.startDate = startDate;
//         this.endDate = endDate;
//         this.monthlyRent = monthlyRent;
//         this.paymentDueDate = paymentDueDate;
//         this.securityDeposit = securityDeposit;
//         this.status = "Active";
//     }
// }

// @NearBindgen({})
// class RentContract {
//     agreements: Map<string, RentAgreement> = new Map();
//     tenantRiskScores: Map<string, number> = new Map();


//     // AI-Based Tenant Risk Assessment
//     @call({})
//     assessTenantRisk(tenantId: string, paymentHistory: number[], latePayments: number, evictionHistory: number): void {
//         let riskScore = this.calculateRiskScore(paymentHistory, latePayments, evictionHistory);
//         this.tenantRiskScores.set(tenantId, riskScore);
//     }

//     @view({})
//     getTenantRiskScore(tenantId: string): number {
//         return this.tenantRiskScores.get(tenantId) || 50; // Default score if not available
//     }

//     private calculateRiskScore(paymentHistory: number[], latePayments: number, evictionHistory: number): number {
//         let consistencyScore = paymentHistory.reduce((a, b) => a + b, 0) / paymentHistory.length;
//         let riskScore = 100 - (consistencyScore * 70) - (latePayments * 10) - (evictionHistory * 20);
//         return Math.max(0, Math.min(100, riskScore));
//     }
// }
