# -*- coding: utf-8 -*-

# (c) 2019 - 2024 Open Risk, all rights reserved
#
# openSecuritisation is licensed under the Apache 2.0 license a copy of which is included
# in the source distribution of TransitionMatrix. This is notwithstanding any licenses of
# third-party software included in this distribution. You may not use this file except in
# compliance with the License.
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.

"""

Inputs:
- Serialized Structure in YAML file
- Asset Cashflow Scenario in pickled file
- Stored Lambda functions in YAML file

"""

import pickle

import numpy as np
from ruamel.yaml import YAML

###################################################
# Load Serialized structure from file
###################################################

in_yaml = YAML(typ='unsafe')
inFile = open('outstructure.yml', 'r')
S = in_yaml.load(inFile)
inFile.close()

###################################################
# Load Pickled scenario data from file
###################################################

A = pickle.load(open("asset_scenario.pkl", 'rb'))


# Define some aliases for conciseness
# Number of periods (including final repayment period)
N = A.periods
# Number of issued bonds
M = len(S.Liabilities)
# Number of OC/IC test pairs
T = S.Tests

# Initialize all dynamic cashflow arrays to zero (placeholders)
# - actual bond / equity payments
# - scheduled bond payments
# - collateralisation test indicators etc
S.initialize(N)

# Auxiliary arrays (temporary within period)
# Required notional reduction (OC) per Trigger and Bond (current period)
# Required payment reduction (IC) per Trigger and Bond (current period)
Bond_Reduction = np.zeros((T, M))
Payment_Reduction = np.zeros((T, M))
# Whether failing test has been cured after application of available cashflows
Cure_Status = np.zeros(T)

###################################################
# Load lambda functions from file
###################################################

lambdas_yaml = YAML(typ='unsafe')
Lambdas_File = open('lambda_dictionary.yml', 'r')
Lambda_Dict = lambdas_yaml.load(Lambdas_File)
Lambdas_File.close()

# Create function objects (and help strings)
F = {}
F_help = {}
for l in Lambda_Dict:
    print(l)
    F[l] = eval(Lambda_Dict[l]['function'])
    F_help[l] = Lambda_Dict[l]['description']

###################################################
# Waterfall Execution
###################################################


# For all periods before final distributions
for k in range(N):

    # Regular period cashflows
    if k < N - 1:

        print("=-" * 40)
        print("Period ", k)
        print("=-" * 40)

        # update scheduled payments for all bonds
        print("Principal and Scheduled Bond Payments")
        print("." * 80)
        for i in range(M):
            B = S.Liabilities[i]
            B.Payment[k] = 0.0
            if k == 0:
                B.Notional[0] = B.initial_Notional
            else:
                B.Notional[k] = B.Notional[k - 1]

            # B.Scheduled_Payment[k] = (A.r + B.Bond_Spread) * B.Notional[k]
            B.Scheduled_Payment[k] = F["floating_rate_payment"](A.r, B.Bond_Spread, B.Notional[k])
            print('Bond ', B.Indicator, B.Notional[k], B.Scheduled_Payment[k])
        print("." * 80)

        # ------------------------------------------------
        # STAGE 1: Senior Waterfall
        # ------------------------------------------------

        # available interest proceeds (subtract fees from available) and principal proceeds
        # interest_proceeds = max(0.0, A.interest_proceeds[k] - S.senior_fees)
        interest_proceeds = F["subtract_amount"](A.interest_proceeds[k], S.senior_fees)
        principal_proceeds = A.principal_proceeds[k]
        print('Senior Waterfall')
        print('Interest Proceeds : ', interest_proceeds)
        print('Principal Proceeds : ', principal_proceeds)

        # Simplifying assumption that there is only one Senior Bond receiving payments as per
        # the senior waterfall segment
        for i in range(M):
            B = S.Liabilities[i]
            if B.Type == 'Senior':
                # Calculate Actual Payment on the basis of available cashflow
                # Any Payment Shortfall Deferred
                # Adjustment to interest and principal proceeds
                actual_payment1 = min(B.Scheduled_Payment[k], interest_proceeds)
                actual_payment2 = min(B.Scheduled_Payment[k] - actual_payment1, principal_proceeds)
                # B.Payment[k] += actual_payment1 + actual_payment2
                B.Payment[k] += F["collect_payments"](actual_payment1, actual_payment2)
                B.Notional[k] += B.Scheduled_Payment[k] - B.Payment[k]
                # principal_proceeds = max(0.0, principal_proceeds - actual_payment2)
                principal_proceeds = F["subtract_amount"](principal_proceeds, actual_payment2)
                # interest_proceeds = max(0.0, interest_proceeds - actual_payment1)
                interest_proceeds = F["subtract_amount"](interest_proceeds, actual_payment1)
                print("Senior Bond Payment: ", B.Payment[k])
                print("Senior Notional: ", B.Notional[k])
                print("." * 80)
                print('Residual Interest Proceeds : ', interest_proceeds)
                print('Residual Principal Proceeds : ', principal_proceeds)
                print("-" * 80)

        # ------------------------------------------------
        # STAGE 2: Mezzanine Waterfall
        # -----------------------------------------------

        # Loop over all OC/IC tests starting from the most senior
        for i in range(T):

            print('Mezzanine Waterfall')
            print('OC/IC Test : ', i)

            # Step 2a: OC/IC Ratios/Tests and OC/IC Cure Calculations
            # for the i-th OC/IC pair and for Period k
            #
            # Here we make the assumption that there is one OC/IC test for each Bond

            OCTest = S.OC_Tests[i]
            ICTest = S.IC_Tests[i]

            # For each bond
            # Loop over more junior bonds and calculate overcollateralization tests for this period
            running_oc = 0.0
            running_ic = 0.0
            for j in range(i + 1):
                B = S.Liabilities[j]
                running_oc += B.Notional[k]
                running_ic += B.Scheduled_Payment[k]
                # Use adjusted notional
                S.adj_notional[k] = S.OC_haircut * A.notional[k] + principal_proceeds + S.reserve.amount
                # Calculate OC/IC Ratios
                OCTest.OC_Ratio[k] = S.adj_notional[k] / running_oc
                ICTest.IC_Ratio[k] = (interest_proceeds - S.IC_haircut) / running_ic

            print('OC Ratio vs Trigger : ', OCTest.OC_Ratio[k], OCTest.OC_Trigger)
            print('IC Ratio vs Trigger : ', ICTest.IC_Ratio[k], ICTest.IC_Trigger)

            # STEP 2b: Check OC/IC Pass/Fail of Tests

            OCTest.OC_Status[k] = (OCTest.OC_Ratio[k] > OCTest.OC_Trigger)
            ICTest.IC_Status[k] = (ICTest.IC_Ratio[k] > ICTest.IC_Trigger)

            print('OC Status : ', OCTest.OC_Status[k])
            print('IC Status : ', ICTest.IC_Status[k])

            # STEP 2c: IP/PP distributions on the basis of the OC/IC tests
            # Case 2c_1: Passing the i-th (OC, IC) test
            if OCTest.OC_Status[k] == 1 and ICTest.IC_Status[k] == 1:

                # Passing Mezzanine Test
                if i < T - 1:
                    # Pay available interest in i+1 subordinated note.
                    # If there is shortfall, it is added as deferred interest to the bond notional
                    # Adjust interest proceeds
                    # No changes to the available principal proceeds
                    B = S.Liabilities[i + 1]
                    # B.Payment[k] += min(B.Scheduled_Payment[k], interest_proceeds)
                    B.Payment[k] += F["apply_scheduled_payment"](B.Scheduled_Payment[k], interest_proceeds)
                    B.Notional[k] += B.Scheduled_Payment[k] - B.Payment[k]
                    interest_proceeds = max(0.0, interest_proceeds - B.Payment[k])
                    print('Passing Mezzanine Test Cashflows')
                    print(B.Indicator, "Bond Payment: ", B.Payment[k])
                    print(B.Indicator, "Bond Notional: ", B.Notional[k])
                # Passing Junior Test
                else:
                    # Allocation of all proceeds to reserve account (if any)
                    # Make equity payments
                    # S.reserve.amount = (1.0 + A.r) * S.reserve.amount + principal_proceeds
                    S.reserve.amount = F["compound_and_add"](A.r, S.reserve.amount, principal_proceeds)
                    principal_proceeds = 0
                    S.Equity.payment[k] = interest_proceeds
                    interest_proceeds = 0
                    print('Passing Junior Test Cashflows')
                    print("Equity Payment: ", S.Equity.payment[k])

                print("." * 80)
                print('Residual Interest Proceeds : ', interest_proceeds)
                print('Residual Principal Proceeds : ', principal_proceeds)
                print("-" * 80)
            # Case 2c_2: Failing the i-th test (either OC or IC or both)
            else:

                # Entering Mandatory CURE branch
                # Calculate Required Notional Reduction on the Basis of OC Tests
                # TargetNotional is the target notional for bonds senior or equal to the failing OC/IC test
                TargetNotional = S.adj_notional[k] / OCTest.OC_Trigger
                # ActualNotional is the actual current notional for the bonds senior or equal to the OC/IC test
                ActualNotional = 0.0
                for j in range(i + 1):
                    B = S.Liabilities[j]
                    ActualNotional += B.Notional[k]

                # Required Senior Bond OC Test Reduction is calculated first
                B = S.Liabilities[0]
                # Bond_Reduction[i, 0] = max(min(ActualNotional - TargetNotional, B.Notional[k]), 0.0)
                Bond_Reduction[i, 0] = F["required_reduction"](ActualNotional - TargetNotional, B.Notional[k])
                cumulative_reduction = Bond_Reduction[i, 0]
                # For all tranches <= to the OC test, except Senior most bond
                for j in range(1, i + 1):
                    B = S.Liabilities[j]
                    Bond_Reduction[i, j] = max(
                        min(ActualNotional - TargetNotional - cumulative_reduction, B.Notional[k]), 0.0)
                    cumulative_reduction += Bond_Reduction[i, j]

                # Calculate Required Payment Reduction on the Basis of IC Tests
                # This is the target required payment for bonds senior or equal to the OC/IC test
                TargetPayment = (interest_proceeds - S.IC_haircut) / ICTest.IC_Trigger
                # This is the actual scheduled payment for the bonds senior or equal to the OC/IC test
                ActualPayment = 0.0
                for j in range(0, i):
                    B = S.Liabilities[j]
                    ActualPayment += B.Scheduled_Payment[k]

                # Required Senior Most Bond Reduction is calculated first
                B = S.Liabilities[0]
                Payment_Reduction[i, 0] = max(min(ActualPayment - TargetPayment, B.Scheduled_Payment[k]), 0.0)
                cumulative_reduction = Payment_Reduction[i, 0]

                for j in range(1, i + 1):  # For all tranches <= to the IC test, except 0-bond
                    B = S.Liabilities[j]
                    Payment_Reduction[i, j] = max(
                        min(ActualPayment - TargetPayment - cumulative_reduction, B.Scheduled_Payment[k]), 0.0)
                    cumulative_reduction += Payment_Reduction[i, j]

                # Calculate Required Notional Reduction from Required Payment Reduction
                # Then apply maximum required reduction per bond/test
                # For all bonds
                for j in range(M):
                    B = S.Liabilities[j]
                    P_Bond_Reduction = Payment_Reduction[i, j] / (A.r + B.Bond_Spread)
                    Bond_Reduction[i, j] = max(P_Bond_Reduction, Bond_Reduction[i, j])

                # Use available interest income to repay principal of notes sequentially
                # up to the required reduction
                for j in range(i + 1):
                    B = S.Liabilities[j]
                    notional_reduction1 = min(Bond_Reduction[i, j], interest_proceeds)
                    B.Notional[k] = B.Notional[k] - notional_reduction1
                    B.Payment[k] = B.Payment[k] + notional_reduction1
                    Bond_Reduction[i, j] = max(0.0, Bond_Reduction[i, j] - notional_reduction1)
                    interest_proceeds = max(0.0, interest_proceeds - notional_reduction1)

                    # Use available principal income to repay principal of notes sequentially
                    # up to the required reduction
                    notional_reduction2 = min(Bond_Reduction[i, j], principal_proceeds)
                    B.Notional[k] = B.Notional[k] - notional_reduction2
                    B.Payment[k] = B.Payment[k] + notional_reduction2
                    Bond_Reduction[i, j] = max(0.0, Bond_Reduction[i, j] - notional_reduction2)
                    principal_proceeds = max(0.0, principal_proceeds - notional_reduction2)

                # Calculate whether i-th OC/IC cure was successful
                # If bond reductions are complete checksum = 0
                checksum = 0
                for j in range(i + 1):
                    checksum += Bond_Reduction[i, j]

                if checksum > 0:
                    # Case 2c_2_Fail: CURE failed, there should be no more funds
                    Cure_Status[i] = 0
                    if i < T - 1:
                        # Mezzanine Test Failed
                        # Defer interest on current and more junior notes
                        for j in range(i + 1, M):
                            B = S.Liabilities[j]
                            B.Notional[k] = B.Notional[k] + B.Scheduled_Payment[k]
                            print('Failed Test / Failed Cure Mezzanine Test Cashflows')
                            print(B.Indicator, "Bond Payment: ", B.Payment[k])
                            print(B.Indicator, "Bond Notional: ", B.Notional[k])

                    else:
                        # Junior Test Failed
                        # No equity payment this period
                        S.reserve.amount = (1.0 + A.r) * S.reserve.amount + principal_proceeds
                        principal_proceeds = 0
                        S.Equity.payment[k] = 0
                        print('Failed Test / Failed Cure Junior Test Cashflows')
                        print("Equity Payment: ", S.Equity.payment[k])

                else:
                    # Case 2c_2_Sucess: CURE succeeded, here may be some funds left for disbursement
                    Cure_Status[i] = 1
                    if i < T - 1:
                        # Mezzanine Test Cured
                        # Pay available interest in i+1-th subordinated note.
                        # If there is shortfall, it is added as deferred interest to the bond notional
                        # Adjust interest proceeds
                        # No changes to the available principal proceeds
                        B = S.Liabilities[i + 1]
                        B.Payment[k] = B.Payment[k] + min(B.Scheduled_Payment[k], interest_proceeds)
                        B.Notional[k] = B.Notional[k] + B.Scheduled_Payment[k] - B.Payment[k]
                        interest_proceeds = max(0.0, interest_proceeds - B.Payment[k])
                        print('Failed Test / Successful Cure Mezzanine Test Cashflows')
                        print(B.Indicator, "Bond Payment: ", B.Payment[k])
                        print(B.Indicator, "Bond Notional: ", B.Notional[k])
                    else:
                        # Junior Test Cured
                        # Allocation of all principal proceeds to reserve account (if any)
                        # Make equity payments this period
                        S.reserve.amount = (1.0 + A.r) * S.reserve.amount + principal_proceeds
                        principal_proceeds = 0
                        S.Equity.payment[k] = interest_proceeds
                        interest_proceeds = 0
                        print('Failed Test / Successful Cure Junior Test Cashflows')
                        print("Equity Payment: ", S.Equity.payment[k])

                # OC_Cure IF bracket
                # OC_Test IF bracket
                print("." * 80)
                print('Residual Interest Proceeds : ', interest_proceeds)
                print('Residual Principal Proceeds : ', principal_proceeds)
                print("-" * 80)

        # Update Scheduled Payments for all Bonds (to take into account notional changes)
        for j in range(M):
            B = S.Liabilities[j]
            B.Scheduled_Payment[k] = (A.r + B.Bond_Spread) * B.Notional[k]

    # Final period cashflows: Calculate final repayments to bonds and equity
    elif k == N - 1:
        # Assumption: Performing collateral is sold at par and cash added to reserve account
        # Reserve account collects last period recovery and interest proceeds
        S.reserve.amount = (1.0 + A.r) * S.reserve.amount + \
                           A.notional[k] + A.principal_proceeds[k] + A.interest_proceeds[k]

        # Sequential repayment of all bonds
        for B in S.Liabilities:
            B.Scheduled_Payment[k] = (1.0 + A.r + B.Bond_Spread) * B.Notional[k]
            actual_payment = min(B.Scheduled_Payment[k], S.reserve.amount)
            B.Payment[k] = B.Payment[k] + actual_payment
            S.reserve.amount = max(0.0, S.reserve.amount - actual_payment)

        # Residual cash goes to equity
        S.Equity.payment[k] = S.reserve.amount

print("=" * 80)
for j in range(M):
    B = S.Liabilities[j]
    print(B.Indicator, "Bond Payment: ", B.Payment)
    print(B.Indicator, "Bond Notional: ", B.Notional)
    print("." * 80)
print('Equity: ', S.Equity.payment)
