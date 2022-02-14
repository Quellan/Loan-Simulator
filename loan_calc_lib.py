"""Library for simulating Loan Schedules.

Contains classes to describe loans, budgets, lump sum payments and
the result of simulations. See loan_calc.py for examples of use."""

from enum import Enum
from typing import List, Optional

import dataclasses
import math


"""Contains the information needed for a simple non-compounding loan.

Per https://www.firstrepublic.com/articles-insights/life-money/grow-your-wealth/what-is-compound-interest-making-your-money
mortages tend to not use compounding interest.
"""
@dataclasses.dataclass
class Loan:
  name: Optional[str]  # A string used to identify the loan.
  amount: float  # The size of the loan asked for.
  rate: float  # The interest for the fixed term as a percent
  term: int  # The length of the loan in months
  fixed_period: int  # then length of the fixed period in months.
                     # For a fully fixed loan should be at least as large
                     # as the term.
  var_rate: Optional[float] = None # The rate that we are assuming we will see in the
                                   # non-fixed portion of the loan

"""This represents a very simplified bare bones model of a budget.
Intended to try to capture how much extra income will be going to the
mortgage while having simple inflation measures.
"""
@dataclasses.dataclass
class Budget:
  name: Optional[str]  # Used to distinguish this from other budgets if playing with scenarios.
  monthly_income: float  # The amount available for mortages and life.
  salary_rate_increase: float  # A percentage that indicates the expected yearly raise.
  monthly_expenses: float  # Intended to cover food/utilities/etc.
  expenses_rate_increase: float  # A percentage to cover the inflation of expenses.
  monthly_prop_tax: float  # The amount paid in property taxed averagedd per month.
                           # Notably in California this is only altered upon appraisal,
                           # so it is not subject to inflation.
  # What percentage of money leftover after the mortage and expenses are paid will 
  # go to direct payments against the mortgage principal.
  min_principal_payment: float  # If the overflow is less than this number, it will be
                                # saved and added to each month until it is above this
                                # number. The result will be applied to the principal
                                # before the next month's payment.
  month_offset: int = 0  # What month the budget started in. Both salary and expenses are
                         # assumed to increase in december.
  overflow_principal_percent: Optional[float] =  None
  # Ignored if overflow_principal_percent is non-zero. Otherwise represents a 
  # fixed amount of extra money going to the principal each month. This is
  # subject to the expenses rate increase.
  overflow_principal_abs: Optional[float] = None


class PaymentType(Enum):
  DIRECT = 0  # A direct payment to principal that doesn't change the monthly payment.
  REAMORTIZING = 1  # A payment that reamortizes the loan.

"""Intended to capture big one-off payments that are not regularly scheduled."""
@dataclasses.dataclass
class PrincipalPayment:
  type: PaymentType  # Whether the payment is reamortizing or not.
  amount: float
  time: int
  new_loan_terms: Optional[Loan] = None # Used to do the reamortization for a reamortizing
                                        # payment. Reamortized loans ignore the amount field
                                        # here and instead choose the remaining principal as
                                        # the original amount.

"""Captures the relevant information about the loan after some amount of payments."""
@dataclasses.dataclass
class LoanEval:
  loan_name: Optional[str]  # The name of the original loan.
  principal_remaining: float  # The remaining money owed.
  principal_paid: float  # The amount of money paid off.
  interest_paid: float  # The amount of money paid as interest.
  length: int  # How long it took before exiting the loan. If the remaining
               # principal is 0, this means that the loan is paid off in full.
  monthly_payments: List[float]  # The first element is monthly payment at the
                                 # start of the loan. Subsequent elements refer to
                                 # reamortizations.

  def __str__(self):
    return (f"Loan name: \t{self.loan_name}\n"
            f"Principal paid: \t{self.principal_paid:.2f}\n"
            f"Principal remaining: \t{self.principal_remaining:.2f}\n"
            f"Interest paid: \t{self.interest_paid:.2f}\n"
            f"Monthly payments: \t{self.monthly_payments}\n"
            f"Months taken: \t{self.length}\n")

def GetMonthlyPayment(loan: Loan) -> float:
  """Gets the initial monthly payment given the loan parameters."""
  monthly_int = loan.rate / (12 * 100)
  return loan.amount * (
      monthly_int * math.pow(1 + monthly_int, loan.term) /
      (math.pow(1 + monthly_int, loan.term) - 1))

def LoanCalc(loan: Loan, budget: Budget, payments: List[PrincipalPayment],
    exits: List[int], verbose: bool = False) -> List[LoanEval]:
  """Calculate the principal and interest paid on the loan.

  The args are self-explanatory with the exception of exits. Exits is an ascending
  list of integers each of which represents selling the house after that number of
  months. Each output entry corresponds to an exit, and there is a final output entry
  for when the loan is fully paid off.

  If verbose is set, each month we print the total_payment, interest payment and
  remaining principal.
  """
  # We copy all the inputs so that they can be reused across differnt combinations.
  loan = dataclasses.replace(loan)
  budget = dataclasses.replace(budget)
  # This function doesn't modify any of the PrincipalPayment objects so we're fine
  # just shallow copying the list.
  payments = payments[:]
  exits = exits[:]
  monthly_payment = GetMonthlyPayment(loan)
  remaining_principal = loan.amount
  terms_paid = 0
  monthly_int = loan.rate / (12 * 100)
  monthly_var_int = 0.0 if not loan.var_rate else loan.var_rate / (12 * 100)
  fixed_period = loan.fixed_period

  next_lump_sum = None
  if payments:
    payments.reverse()
    next_lump_sum = payments.pop()

  budget_savings = 0

  current_exit = 0
  last_exit = False
  if not exits:
    last_exit = True

  interest_paid = 0.0
  loan_evals = []
  monthly_payments = [monthly_payment]
  if verbose:
    print(f"Initial monthly payment is {monthly_payment:.2f}")

  while remaining_principal > 0:
    # Check if we're exiting this term, if so we won't be paying this term, so we
    # get numbers now.
    if not last_exit and terms_paid == exits[current_exit]:
      current_exit += 1
      last_exit = current_exit == len(exits)
      loan_evals.append(
        LoanEval(
          loan_name=loan.name,
          principal_remaining=remaining_principal,
          principal_paid=loan.amount-remaining_principal,
          interest_paid=interest_paid,
          length=terms_paid,
          monthly_payments=monthly_payment))

    # See if there is a lump_sum to apply to the principal.
    if next_lump_sum and next_lump_sum.time == terms_paid:
      remaining_principal -= next_lump_sum.amount
      if next_lump_sum.type == PaymentType.REAMORTIZING:
        reamor_loan = dataclasses.replace(next_lump_sum.new_loan_terms)
        reamor_loan.amount = remaining_principal
        monthly_payment = GetMonthlyPayment(reamor_loan)
        # Assumed that reamortizing pushes the start of the ARM away. If not
        # this should be solved with the lump sum input.
        reamor_loan.fixed_period += terms_paid
        monthly_int = reamor_loan.rate / (12 * 100)
        monthly_var_int = 0.0 if not reamor_loan.var_rate else reamor_loan.var_rate / (12 * 100)

      if payments:
        next_lump_sum = payments.pop()
      else:
        next_lump_sum = None
    # See if we have a savings payment to apply to the principal.
    if budget_savings > budget.min_principal_payment:
      remaining_principal -= budget_savings
      budget_savings = 0

    # Now we start calculating available monthly money.
    monthly_savings = budget.monthly_income - (
        budget.monthly_expenses + monthly_payment + budget.monthly_prop_tax)
    # Then we do the basic interest calculations.
    interest = monthly_int * remaining_principal
    interest_paid += interest
    # If we're past the fixed rate period, the additional interest gets added
    # onto the interest paid. But since we're modelling the additional interest
    # as an increase in monthly payment, we keep the original payment and interest
    # when it comes to decreasing the principal. Ie. the variable rate means more
    # interest costs but no change in loan payment schedule.
    if terms_paid >= fixed_period:
      extra_interest = (monthly_var_int - monthly_int) * remaining_principal
      monthly_savings -= extra_interest
      interest_paid += extra_interest
    remaining_principal -= monthly_payment - interest

    # Now we see if there's any money left to go to mortgage payments.
    if budget.overflow_principal_percent is not None:
      budget_savings += monthly_savings * (budget.overflow_principal_percent / 100)
    elif budget.overflow_principal_abs:
      budget_savings += min(monthly_savings, budget.overflow_principal_abs)

    terms_paid += 1
    if verbose:
      print(f"After {terms_paid} months, monthly payment is {monthly_payment:.2f}, "
            f"interest this month was {interest:.2f}, total interest is "
            f"{interest_paid:.2f} and there is {remaining_principal:.2f} left.")
      if budget_savings > budget.min_principal_payment:
        print(f"Next month we will remove a lump sum of {budget_savings:.2f} from "
              f"the principal.")

    # Now we need to check if the budget terms change.
    if ((terms_paid + budget.month_offset) % 12) == 0:
      budget.monthly_income *= (1 + budget.salary_rate_increase / 100.0)
      budget.monthly_expenses *= (1 + budget.expenses_rate_increase / 100.0)
      if verbose:
        print(f"New monthly income: {budget.monthly_income:.2f} "
              f"New monthly expenses: {budget.monthly_expenses:.2f}")

  loan_evals.append(
    LoanEval(
      loan_name=loan.name,
      principal_remaining=remaining_principal,
      principal_paid=loan.amount-remaining_principal,
      interest_paid=interest_paid,
      length=terms_paid,
      monthly_payments=monthly_payment))
  return loan_evals
