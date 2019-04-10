# -*- coding: utf-8 -*-

# (c) 2019 Open Risk, all rights reserved
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

""" This module provides the key transition matrix objects

* CreditCurve_ implements the functionality of a collection of credit (default curves)
* TransitionMatrix_ implements the functionality of single period transition matrix
* TransitionMatrixSet_ provides a container for a multiperiod transition matrix collection
* StateSpace holds information about the stochastic system state space
* EmpiricalTransitionMatrix implements the functionality of a continuously observed transition matrix

"""

import numpy as np

class Structure:
    def __init__(self):
        """ The AssetScenario object implements a typical collection of `credit curves <https://www.openriskmanual.org/wiki/Credit_Curve>`_.
        The class inherits from numpy matrices and implements additional properties specific to curves.

        NB: This part is outside the openSecuritisation specification - any approach that produces suitable
        portfolio cashflow streams, whether aggregating from loan-level calculations or as portfolio-level model
        is equally valid

        """
        # Liability Structure
        self.Liabilities = None
        self.Equity = None
        # Structural Elements
        self.reserve = None
        self.Tests = None
        self.OC_Tests = None
        self.IC_Tests = None
        self.IC_haircut = 0.0
        self.OC_haircut = 1.0
        # Other Static fields
        self.FeeStructure = None
        self.senior_fees = 0.0025
        # Dynamic fields
        self.adj_notional = None

    def calculate_equity(self, initial_notional):
        """
        Simulate a default rate process

        """
        # Implement the accounting identity that defines equity as the
        # residual interest in asset pool
        equity = initial_notional
        for Bond in self.Liabilities:
            # print(equity, Bond.initial_Notional)
            equity = equity - Bond.initial_Notional
        self.Equity.amount = equity

    def initialize(self, N):
        """
        Initialize all dynamic cashflow arrays to zero (placeholders)
        - actual bond / equity payments
        - scheduled bond payments
        - collateralisation test indicators etc
        """

        self.Equity.payment = np.zeros(N)
        for i in range(len(self.Liabilities)):
            B = self.Liabilities[i]
            B.Payment = np.zeros(N)
            B.Scheduled_Payment = np.zeros(N)
            B.Notional = np.zeros(N)

        self.adj_notional = np.zeros(N)
        for i in range(self.Tests):
            OCTest = self.OC_Tests[i]
            OCTest.OC_Ratio = np.zeros(N)
            OCTest.OC_Status = np.zeros(N)
            ICTest = self.IC_Tests[i]
            ICTest.IC_Ratio = np.zeros(N)
            ICTest.IC_Status = np.zeros(N)


class Liability:
    pass


class Collateralization_Test:
    pass


class Bond(Liability):
    def __init__(self):
        # Static fields
        self.initial_Notional = 0.0
        self.scheduled_Payment = 0.0
        self.spread = 0.0
        self.OC_Trigger = 0.0
        self.IC_Trigger = 0.0
        self.Rank = None
        self.Type = None
        self.Indicator = None
        # Dynamic fields
        self.Notional = None
        self.Payment = None
        # self.required_notional_reduction = 0.0
        # self.required_payment_reduction = 0.0


class Equity(Liability):
    def __init__(self):
        # Static Fields
        self.amount = 0.0
        # Equity cashflows
        self.payment = None


class Reserve(Liability):
    def __init__(self):
        self.amount = 0.0


#
#  Collateralization Tests (Interest and Principal)
#

class OC_Test(Collateralization_Test):
    def __init__(self):
        # Static fields
        self.OC_Trigger = 0.0
        # Dynamic fields
        self.OC_Ratio = None
        self.OC_Status = None


class IC_Test(Collateralization_Test):
    def __init__(self):
        # Static fields
        self.IC_Trigger = 0.0
        # Dynamic fields
        self.IC_Ratio = None
        self.IC_Status = None
