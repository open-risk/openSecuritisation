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


import numpy as np

from AssetScenario import AssetScenario

###################################################
# Create and store an Asset Scenario
###################################################

A = AssetScenario(n=20)
A.create()

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

A.save("asset_scenario.pkl")
