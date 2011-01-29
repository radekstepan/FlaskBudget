#!/usr/bin/python
# -*- coding: utf -*-

# setup
import unittest

# test cases
from tests.users import UsersTestCases
from tests.accounts import AccountsTestCases
from tests.income import IncomeTestCases
from tests.expenses import ExpensesTestCases

if __name__ == '__main__':
    #suite = unittest.TestLoader().loadTestsFromTestCase(UsersTestCases)
    #unittest.TextTestRunner(verbosity=3).run(suite)
    #print "\n"
    #suite = unittest.TestLoader().loadTestsFromTestCase(AccountsTestCases)
    #unittest.TextTestRunner(verbosity=3).run(suite)
    #print "\n"
    #suite = unittest.TestLoader().loadTestsFromTestCase(IncomeTestCases)
    #unittest.TextTestRunner(verbosity=3).run(suite)
    #print "\n"
    suite = unittest.TestLoader().loadTestsFromTestCase(ExpensesTestCases)
    unittest.TextTestRunner(verbosity=3).run(suite)
    print "\n"