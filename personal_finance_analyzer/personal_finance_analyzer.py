"""Personal financial analyzer.

This project is being designed and implemented one component at a time using
the existing Business Financial Analyzer as its architectural foundation.
"""

from __future__ import annotations

from enum import Enum


class PersonalFinanceCategory(str, Enum):
    """Approved top-level categories for personal financial activity."""

    housing = "Housing"
    utilities = "Utilities"
    groceries = "Groceries"
    dining_out = "Dining Out"
    transportation = "Transportation"
    fuel = "Fuel"
    insurance = "Insurance"
    healthcare = "Healthcare"
    debt_payments = "Debt Payments"
    subscriptions = "Subscriptions"
    shopping = "Shopping"
    entertainment = "Entertainment"
    travel = "Travel"
    education = "Education"
    personal_care = "Personal Care"
    childcare_or_family = "Childcare or Family"
    gifts_and_donations = "Gifts and Donations"
    taxes_and_fees = "Taxes and Fees"
    savings = "Savings"
    investments = "Investments"
    cash_withdrawals = "Cash Withdrawals"
    miscellaneous = "Miscellaneous"
    transfers = "Transfers"
    income = "Income"


class CashFlowType(str, Enum):
    """Approved ways a transaction can affect personal financial analysis."""

    income = "Income"
    spending = "Spending"
    debt_payment = "Debt Payment"
    credit_card_payment = "Credit Card Payment"
    internal_transfer = "Internal Transfer"
    external_transfer = "External Transfer"
    savings_contribution = "Savings Contribution"
    savings_withdrawal = "Savings Withdrawal"
    investment_contribution = "Investment Contribution"
    investment_withdrawal = "Investment Withdrawal"
    refund = "Refund"
    reimbursement = "Reimbursement"
    cash_withdrawal = "Cash Withdrawal"
    zero_amount = "Zero Amount"
    uncertain = "Uncertain"


personal_finance_subcategories: dict[
    PersonalFinanceCategory,
    tuple[str, ...],
] = {
    PersonalFinanceCategory.housing: (
        "Rent",
        "Mortgage Payment",
        "Property Tax",
        "Homeowners Association",
        "Home Maintenance",
        "Home Improvement",
        "Household Services",
        "Other Housing",
    ),
    PersonalFinanceCategory.utilities: (
        "Electricity",
        "Natural Gas",
        "Water and Sewer",
        "Internet",
        "Mobile Phone",
        "Trash",
        "Other Utilities",
    ),
    PersonalFinanceCategory.groceries: (
        "Supermarket",
        "Warehouse Club",
        "Convenience Store",
        "Meal Ingredients",
        "Other Groceries",
    ),
    PersonalFinanceCategory.dining_out: (
        "Restaurant",
        "Fast Food",
        "Coffee Shop",
        "Takeout and Delivery",
        "Bar",
        "Other Dining",
    ),
    PersonalFinanceCategory.transportation: (
        "Public Transit",
        "Rideshare",
        "Taxi",
        "Parking",
        "Tolls",
        "Vehicle Maintenance",
        "Vehicle Registration",
        "Other Transportation",
    ),
    PersonalFinanceCategory.fuel: (
        "Gasoline",
        "Electric Vehicle Charging",
        "Other Fuel",
    ),
    PersonalFinanceCategory.insurance: (
        "Auto",
        "Health",
        "Renters",
        "Homeowners",
        "Life",
        "Disability",
        "Other Insurance",
    ),
    PersonalFinanceCategory.healthcare: (
        "Doctor",
        "Dental",
        "Vision",
        "Pharmacy",
        "Therapy",
        "Medical Equipment",
        "Other Healthcare",
    ),
    PersonalFinanceCategory.debt_payments: (
        "Mortgage Loan",
        "Auto Loan",
        "Student Loan",
        "Personal Loan",
        "Medical Debt",
        "Other Debt",
    ),
    PersonalFinanceCategory.subscriptions: (
        "Streaming",
        "Software",
        "Gaming",
        "News and Media",
        "Membership",
        "Other Subscription",
    ),
    PersonalFinanceCategory.shopping: (
        "Clothing",
        "Electronics",
        "Household Goods",
        "Online Retail",
        "General Merchandise",
        "Other Shopping",
    ),
    PersonalFinanceCategory.entertainment: (
        "Movies",
        "Events",
        "Hobbies",
        "Recreation",
        "Games",
        "Other Entertainment",
    ),
    PersonalFinanceCategory.travel: (
        "Airfare",
        "Lodging",
        "Rental Car",
        "Vacation Transportation",
        "Travel Activities",
        "Other Travel",
    ),
    PersonalFinanceCategory.education: (
        "Tuition",
        "Books",
        "Courses",
        "School Supplies",
        "Student Fees",
        "Other Education",
    ),
    PersonalFinanceCategory.personal_care: (
        "Haircare",
        "Cosmetics",
        "Spa",
        "Fitness",
        "Hygiene",
        "Other Personal Care",
    ),
    PersonalFinanceCategory.childcare_or_family: (
        "Daycare",
        "Babysitting",
        "School Expenses",
        "Child Support",
        "Family Support",
        "Other Family Expense",
    ),
    PersonalFinanceCategory.gifts_and_donations: (
        "Gifts",
        "Charitable Donations",
        "Religious Donations",
        "Other Giving",
    ),
    PersonalFinanceCategory.taxes_and_fees: (
        "Income Tax",
        "Bank Fee",
        "Late Fee",
        "Government Fee",
        "Professional Fee",
        "Other Tax or Fee",
    ),
    PersonalFinanceCategory.savings: (
        "Savings Contribution",
        "Emergency Fund Contribution",
        "Certificate of Deposit",
        "Other Savings",
    ),
    PersonalFinanceCategory.investments: (
        "Brokerage Contribution",
        "Retirement Contribution",
        "Investment Purchase",
        "Other Investment",
    ),
    PersonalFinanceCategory.cash_withdrawals: (
        "ATM Withdrawal",
        "Cash Back",
        "Other Cash Withdrawal",
    ),
    PersonalFinanceCategory.miscellaneous: (
        "Unclassified Purchase",
        "Other Personal Expense",
    ),
    PersonalFinanceCategory.transfers: (
        "Internal Account Transfer",
        "Credit Card Payment",
        "External Transfer",
        "Uncertain Transfer",
    ),
    PersonalFinanceCategory.income: (
        "Paycheck",
        "Freelance Income",
        "Benefits",
        "Pension",
        "Interest",
        "Dividend",
        "Refund",
        "Reimbursement",
        "Gift Received",
        "Other Income",
    ),
}