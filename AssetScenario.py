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

import numpy as np


class AssetScenario(object):
    def __init__(self, n=10):
        """ The AssetScenario object implements a typical collection of `credit curves <https://www.openriskmanual.org/wiki/Credit_Curve>`_.
        The class inherits from numpy matrices and implements additional properties specific to curves.

        NB: This part is outside the openSecuritisation specification - any approach that produces suitable
        portfolio cashflow streams, whether aggregating from loan-level calculations or as portfolio-level model
        is equally valid

        """

        # The number of periods to calculate
        self.periods = n
        # The net spread earned on credit assets
        self.asset_spread = 0.1
        # The risk free rate
        self.r = 0.0
        # The initial notional value of the portfolio
        self.initial_notional = 1.0
        # Average default rate
        self.mean_default_rate = None
        # Default rate volatility
        self.std_default_rate = None
        # Realized default rate process
        self.conditional_default_rate = np.zeros(n)
        # Recovery rate (deterministic)
        self.recovery = 0.30
        # Principal proceeds process
        self.principal_proceeds = np.zeros(n)
        # Interest proceeds process
        self.interest_proceeds = np.zeros(n)
        # Portfolio notional process
        self.notional = np.zeros(n)

    # def __new__(cls, filepath=None, *args, **kwargs):
    #     if filepath:
    #         with open(filepath) as f:
    #            inst = pickle.load(f)
    #         if not isinstance(inst, cls):
    #            raise TypeError('Unpickled object is not of type {}'.format(cls))
    #     else:
    #         inst = super(AssetScenario, cls).__new__(cls, *args, **kwargs)
    #     return inst

    def create(self):
        """
        Simulate a default rate process

        """

        self.mean_default_rate = 0.0
        self.std_default_rate = 0.0

        # Calculate a default rate process for all periods
        dr = np.random.normal(self.mean_default_rate, self.std_default_rate, self.periods)
        self.conditional_default_rate = np.around(np.clip(dr, a_min=0.0, a_max=None), decimals=3)

        # Initialize the outstanding notional
        self.notional[0] = self.initial_notional
        self.principal_proceeds[0] = 0.0
        self.interest_proceeds[0] = 0.0

        # Iterate over all periods BEFORE maturity
        for k in range(0, self.periods):
            if k == 0:
                self.notional[k] = (1.0 - self.conditional_default_rate[k]) * self.initial_notional
                self.principal_proceeds[k] = self.conditional_default_rate[k] * self.recovery * self.initial_notional
            else:
                self.notional[k] = (1.0 - self.conditional_default_rate[k]) * self.notional[
                    k - 1]
                self.principal_proceeds[k] = self.conditional_default_rate[k] * self.recovery * \
                                             self.notional[k]

        # Interest Proceeds are from outstanding notional at end of period
        for k in range(0, self.periods):
            self.interest_proceeds[k] = (self.r + self.asset_spread) * self.notional[k]

        # End of Final period cashflows (repayment)
        self.principal_proceeds[self.periods - 1] = self.notional[self.periods - 1]
        self.notional[self.periods - 1] = 0.0

        self.notional = np.around(self.notional, decimals=3)
        self.principal_proceeds = np.around(self.principal_proceeds, decimals=3)
        self.interest_proceeds = np.around(self.interest_proceeds, decimals=3)

    def save(self, file):
        output = open(file, 'wb')
        # Pickle the object using the highest protocol available.
        pickle.dump(self, output, -1)
        output.close()
