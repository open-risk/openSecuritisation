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


import pickle

from ruamel.yaml import YAML

from Securitisation import *

####################################################################
# Part 1:
# Structure Specification
#
# For simplicity bonds are assumed in order of decreasing seniority
####################################################################

# Instantiate a securitisation structure
outStruct = Structure()

# Create and add a number of bonds
Bond1 = Bond()
Bond1.Bond_Spread = 0.020
Bond1.initial_Notional = 0.75
Bond1.Type = 'Senior'
Bond1.Indicator = 'A1'

Bond2 = Bond()
Bond2.Bond_Spread = 0.050
Bond2.initial_Notional = 0.10
Bond2.Type = 'Mezzanine'
Bond2.Rank = 1
Bond2.Indicator = 'M1'

Bond3 = Bond()
Bond3.Bond_Spread = 0.100
Bond3.initial_Notional = 0.05
Bond3.Type = 'Mezzanine'
Bond3.Rank = 2
Bond3.Indicator = 'M2'

Bond4 = Bond()
Bond4.Bond_Spread = 0.150
Bond4.initial_Notional = 0.05
Bond4.Type = 'Mezzanine'
Bond4.Rank = 3
Bond4.Indicator = 'M3'

# Equity and Reserve Accounts
equity = Equity()

reserve = Reserve()
reserve.amount = 0.0

# OC Test Specifications
OCTest1 = OC_Test()
OCTest1.OC_Trigger = 1.20

OCTest2 = OC_Test()
OCTest2.OC_Trigger = 1.10

OCTest3 = OC_Test()
OCTest3.OC_Trigger = 1.08

OCTest4 = OC_Test()
OCTest4.OC_Trigger = 1.01

# IC Test Specifications
ICTest1 = IC_Test()
ICTest1.IC_Trigger = 1.0

ICTest2 = IC_Test()
ICTest2.IC_Trigger = 1.0

ICTest3 = IC_Test()
ICTest3.IC_Trigger = 1.0

ICTest4 = IC_Test()
ICTest4.IC_Trigger = 1.0

# Put all liabilities and tests together
outStruct.Liabilities = [Bond1, Bond2, Bond3, Bond4]
outStruct.OC_Tests = [OCTest1, OCTest2, OCTest3, OCTest4]
outStruct.IC_Tests = [ICTest1, ICTest2, ICTest3, ICTest4]
outStruct.Tests = len(outStruct.Liabilities)
outStruct.Equity = equity
outStruct.reserve = reserve

###################################################
# Part 2a  Load an Asset Scenario
#
# Equity is defined implicitly as the residual interest
# Defining this liability fully requires that an asset pool / scenario has been specified
###################################################

A = pickle.load(open("asset_scenario.pkl", 'rb'))

print("=" * 80)
print("Asset Scenario")
print("-" * 80)
print("Initial Notional: ", A.initial_notional)
print("Outstanding Notional: ", A.notional)
print("Default Rate: ", A.conditional_default_rate)
print("Principal Proceeds: ", A.principal_proceeds)
print("Interest Proceeds: ", A.interest_proceeds)
print("-" * 80)
print("Total Principal: ", np.sum(A.principal_proceeds))
print("Total Interest: ", np.sum(A.interest_proceeds))
print("=" * 80)

###################################################
# Part 2b  Initialize Equity
###################################################
outStruct.calculate_equity(A.initial_notional)

###################################################
# Part 3:
# Waterfall Serialization
###################################################


out_yaml = YAML(typ='unsafe')
out_yaml.default_flow_style = False
outFile = open('outstructure.yml', 'w')
out_yaml.dump(outStruct, outFile)
outFile.close()
