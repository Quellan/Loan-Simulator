"""Loan Schedule Simulator.

This was developed to aid in evaluating mortgage options in California. The most
notable way this is Californian is that it assumes property taxes are constant,
since the authour believes that in California they are only updated upon
appraisal of the house.

If should be more flexible than the online spreadsheets the author found since
it allows one to schedule lump sum payments to the principal; and also to set
up a budget that has regular payments to the principal as a function of how much
money is saved.

In order to run this, at a minimum one needs a budget object and a loan object.
In the budget object one can set a monthly income, monthly expenses, and monthly
property taxes. The latter is seperate from the former since property taxes are
not subject to interest. The rate of increase for the salary and expenses can be
toggled as a percentage. This happens every 12 months, and there is a month_offset
toggle to change on what months this happens. If month_offset is 1, we assume the
loan period started in February, and so salary_increases and inflation will happen
on month 11, 23, etc.. Beyond that there are two ways of applying savings to
the principal. overflow_principal_percent lets you divert a percentage of savings
to the principal; while overflow_principal_abs will let you divert a monthly
fixed amount of savings to the principal. (If you do not save enough to hit the
fixed amount, all of your savings will be applied to the principal). When the
savings exceed min_principal_payment they are applied to the principal as a lump
sum before the next monthly payment.

The loan object does not support points or prepayment penalties since the loan
options the authour was considering do not support either of these. The term
is in months and the rate is a percentage. For ARM loans, there is a var_rate
parameter that is used to estimate the average rate once the ARM loan exits the
fixed interest portion of the loan. loan_calc_lib.LoanCalc has a long comment
that explains how the variable rate is treated as sort of a surcharge since the
authour isn't quite sure how they actually work.

In addition to using monthly savings, one can schedule lump_sums to be made against
the principal if one is expecting windfalls and chooses to apply those to the
mortgage. These lump sums can be reamortizing or not, although if they are new
term lengths and interest need to be provided.

Finally, one can provide exit times to the loan. This will let you see how much
principal is left, how much interest has been paid, etc. at any point during the
loan's payment schedule. This is meant to allow one to see the effects of a
mortage schedule is one sells the house before the loan is fully repaid.

The authour is not a financial advisor and this program shouldn't be considered
financial advice. It is at best a simple mental model used by the authour to try
and understand their own situation.

Running this program will print example outputs to the terminal, and hopefully
the setting up of objects is understandable enough. The numbers in the examples
were chosen arbitrarily and are not meant to be realistic or useful.
"""


import loan_calc_lib


if __name__ == "__main__":
    budget = loan_calc_lib.Budget(
            name="Example Budget",
            monthly_income=6000,
            salary_rate_increase=3.5,
            monthly_expenses=2000,
            expenses_rate_increase=3.5,
            monthly_prop_tax=1000,
            overflow_principal_percent=50.0,
            min_principal_payment=1000.0,
            month_offset=0)
    thirty_yr_fixed = loan_calc_lib.Loan(
            name="30 year fixed",
            amount=1000000,
            rate=3.5,
            term=12 * 30,
            fixed_period=12 * 30)
    ten_yr_arm = loan_calc_lib.Loan(
            name="10 year ARM",
            amount=1000000,
            rate=3.4,
            term=12 * 30,
            fixed_period=12 * 10,
            var_rate=6.0)
    seven_yr_arm = loan_calc_lib.Loan(
            name="7 year ARM",
            amount=1000000,
            rate=3.3,
            term=12 * 30,
            fixed_period=12 * 7,
            var_rate=6.0)
    lump_sums = [
            loan_calc_lib.PrincipalPayment(
                type=loan_calc_lib.PaymentType.DIRECT,
                amount=50000,
                time=12)]
    exits = [7*12, 10*12]
    for (loan) in loan_calc_lib.LoanCalc(thirty_yr_fixed, budget, lump_sums, exits, False):
        print(loan)
    for (loan) in loan_calc_lib.LoanCalc(ten_yr_arm, budget, lump_sums, exits, False):
        print(loan)
    for (loan) in loan_calc_lib.LoanCalc(seven_yr_arm, budget, lump_sums, exits, False):
        print(loan)

    lump_sums[-1].type = loan_calc_lib.PaymentType.REAMORTIZING
    lump_sums[-1].new_loan_terms = loan_calc_lib.Loan(
            name="30 year fixed",
            amount=1000000,  # This is ignored.
            rate=3.3,
            term=12 * 30,
            fixed_period=12 * 30)

    for (loan) in loan_calc_lib.LoanCalc(thirty_yr_fixed, budget, lump_sums, exits, False):
        print(loan)
    for (loan) in loan_calc_lib.LoanCalc(seven_yr_arm, budget, [], [], False):
        print(loan)
    for (loan) in loan_calc_lib.LoanCalc(thirty_yr_fixed, budget, [], [10*12, 15*12], False):
        print(loan)
