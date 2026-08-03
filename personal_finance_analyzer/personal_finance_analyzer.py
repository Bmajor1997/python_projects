# Project Name: Personal Spending Analyzer
# ============================================================
# IMPORTS
# ============================================================
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch
from pathlib import Path
from matplotlib.path import Path as MplPath
from pathlib import Path
from tkinter import filedialog
import tkinter as tk
import numpy as np
# ============================================================
# APPLICATION INFORMATIONS
# ============================================================
application_version = "Beta version 2.0"
program_title = "Financial Insights Report"
# ============================================================
# USER INTERFACES
# ============================================================
divider = "=" * 60
welcome_message = (
    "Welcome!\n\n"
    "This application analyzes bank-exported Excel files and\n"
    "provides financial summaries and visualizations."
)
# ============================================================
# ERROR MESSAGES
# ============================================================
file_not_found_error = "The selected file could not be found."
no_file_selected_error = "No file path was provided."
invalid_file_type_error = "The selected file is not a XLSX file."
empty_file_error = "The selected XLSX file is empty."
missing_columns_error = "The XLSX file is missing one or more required columns."
invalid_bank_file_error = "The selected file is not a valid bank transaction."
invalid_transaction_data_error = (
    "The transaction data contains invalid values. "
    "Please correct the XLSX and try again."
)
xlsx_open_error = "File could not be opened."
# ============================================================
# FILE DIALOG CONSTANTS
# ============================================================
file_dialog_title = "Select Your Bank XLSX File"
xlsx_file_types = [("XLSX Files", "*.xlsx")]
no_file_selected_message = (
    "No file was selected.\n\n"
    "Please select a bank XLSX file to continue."
)
#=============================================================
# GLOBAL CONSTANTS
#=============================================================
very_healthy_status = "Very Healthy"
healthy_status = "Healthy"
needs_attention_status = "Needs Attention"
caution_status = "Caution"
weak_status = "Weak"
at_risk_status = "At Risk"
very_weak_status = "Very Weak"
unable_to_determine_status = "Unable to Determine"

income_transaction_type = "Income"
expense_transaction_type = "Expense"
transfer_transaction_type = "Transfer"
zero_amount_transaction_type = "Zero Amount"

default_transfer_identifiers = [
    "internal transfer",
    "account transfer"
]

user_transfer_identifiers = [
    "moneylink"
]
not_a_transfer = "Not a Transfer"
personal_transfer = "Personal Transfer"
owned_account_transfer = "Owned-Account Transfer"
unclassified_transfer = "Unclassified Transfer"
other_income_category = "Other Income"
other_expense_category = "Other Expense"
income_transaction_type = "Income"
expense_transaction_type = "Expense"
zero_amount_transaction_type = "Zero Amount"

housing_category = "Housing"
utilities_category = "Utilities"
healthcare_category = "Healthcare"
transportation_category = "Transportation"
groceries_category = "Groceries"
dining_category = "Dining"
entertainment_category = "Entertainment"
shopping_category = "Shopping"
employment_income_category = "Employment Income"
refund_reimbursement_category = "Refund or Reimbursement"
# ============================================================
# DISPLAY FUNCTIONS
# ============================================================
def display_welcome_screen():


    print(divider)
    print(program_title)
    print(application_version)
    print(divider)
    print(welcome_message)
    print(divider)
# ============================================================
# FILE SELECTION AND VALIDATION FUNCTIONS
# ============================================================
def select_xlsx_file():

    root = tk.Tk()
    root.withdraw()

    selected_file = filedialog.askopenfilename(
        title=file_dialog_title,
        filetypes=xlsx_file_types
    )

    root.destroy()

    if not selected_file:
        return None

    return selected_file
def validate_xlsx_file(selected_file):
    
    xlsx_path = Path(selected_file)

    if not xlsx_path.exists():
        raise Exception(no_file_selected_error)

    if xlsx_path.suffix != ".xlsx":
        raise Exception(invalid_file_type_error)

    if xlsx_path.stat().st_size == 0:
        raise Exception(empty_file_error)

    return xlsx_path
def validate_xlsx_files(selected_files):
    pass
def open_xlsx(xlsx_path):

    try:
        xlsx_file = pd.read_excel(xlsx_path)
    except Exception:
        print(xlsx_open_error)
        return None

    return xlsx_file
def open_xlsx_files(xlsx_paths):
    pass
# ============================================================
# COLUMN IDENTIFICATION FUNCTIONS
# ============================================================
def identify_date_column(xlsx_file):
    possible_date_column_names = [
        "date",
        "transaction date",
        "posted date",
        "posting date",
        "post date",
        "trans date",
        "transaction_date",
        "posting_date",
        "date posted",
        "effective date",
        "activity date",
        "processed date",
        "processing date"
    ]

    no_date_column_found_error = "No Date Column Found."

    normalized_columns = (xlsx_file.columns.str.strip().str.lower())

    possible_date_columns = pd.Index(possible_date_column_names)

    matching_columns = normalized_columns.intersection(
        possible_date_columns
    )

    if len(matching_columns) == 0:
        raise ValueError(no_date_column_found_error)

    matching_column_name = matching_columns[0]

    column_position = normalized_columns.get_loc(
        matching_column_name
    )

    date_column_name = xlsx_file.columns[column_position]

    return date_column_name
def determine_date_range(xlsx_file,date_column_name ):

    # Create error message
    no_dates_found_error = "No Dates Were Found."

    # Retrieve the transaction date column
    date_values = xlsx_file[date_column_name]

    # Convert all values to datetime
    date_values = pd.to_datetime(date_values, errors="coerce")

    #  Remove invalid dates
    date_values = date_values.dropna()

    #Verify at least one valid date remains
    if len(date_values) == 0 :
        raise ValueError(no_dates_found_error)

    start_date = date_values.min()
    end_date = date_values.max()

    return start_date, end_date
def identify_amount_column(xlsx_file):

    possible_amount_column_names = [
        "amount",
        "transaction amount",
        "transaction_amount",
        "value",
        "transaction value",
        "payment amount"
    ]

    no_amount_column_found_error = "Could not find Amount column"

    normalized_columns = (xlsx_file.columns.str.strip().str.lower())

    possible_amount_columns = pd.Index(possible_amount_column_names)

    matching_amount = normalized_columns.intersection(possible_amount_columns)

    if len(matching_amount) == 0:
        raise ValueError(no_amount_column_found_error)

    matching_column_name = matching_amount[0]

    column_position = normalized_columns.get_loc(matching_column_name)

    amount_column_name = xlsx_file.columns[column_position]

    return amount_column_name
def identify_description_column(xlsx_file):

     description_column_name = [
            "description",
            "details"
        ]
    
     missing_description_column = "Could not find transaction description column"
     normalized_columns = xlsx_file.columns.str.strip().str.lower()

     matching_columns = normalized_columns.intersection(pd.Index(description_column_name))

     if matching_columns.empty:
        raise ValueError(missing_description_column)

     matching_column_name = matching_columns[0]

     column_position = normalized_columns.get_loc(
        matching_column_name
    )

     description_column_name = (
        xlsx_file.columns[column_position]
    )

     return description_column_name
# ============================================================
# STATEMENT PREPARATION FUNCTIONS
# ============================================================
def standardize_statement_columns(xlsx_file):
    pass
def combine_statements(standardized_statements):
    pass
def remove_duplicate_transactions(combined_transactions):
    pass
def sort_transactions_by_date(combined_transactions):
    pass
def filter_complete_months(combined_transactions):
    pass
def prepare_combined_statement_data(xlsx_files):
    pass
# ============================================================
# TRANSACTION CLASSIFICATION FUNCTIONS
# ============================================================
def create_transfer_rule_map(user_owned_account_identifiers):

   
    invalid_owned_account_error = "Owned account must be provided as a collection of text values."

   
    if user_owned_account_identifiers is None:
        user_owned_account_identifiers = []

    else:
        if user_owned_account_identifiers is not isinstance(list,tuple,set):
            raise TypeError(invalid_owned_account_error) 

    owned_account_values = user_owned_account_identifiers 

    default_personal_transfer_identifiers = {
                "zel to",
                "zel from",
                "zelle to",
                "zelle from",
                "venmo",
                "cash app",
                "cash app payment"
            } 
        
    default_unclassified_transfer_identifiers = {
                "transfer",
                "transfer funds",
                "ach transfer"
            }

    transfer_rule_sources = {
        "Personal transfer identifiers": default_personal_transfer_identifiers,
        "Unclassified transfer identifiers": default_unclassified_transfer_identifiers,
        "owned account transfer": owned_account_values
    }

    transfer_rule_map = {}

    for transfer_subtype, identifiers in transfer_rule_sources.items():

        normalized_identifiers = []
        seen_identifiers = set()

        for identifier in identifiers:

            if not isinstance(identifier,str):
                raise TypeError(invalid_owned_account_error)

            normalized_identifier = identifier.strip().lower()

            if normalized_identifier.empty:
                continue

            if normalized_identifier in seen_identifiers:
                continue

            normalized_identifiers.append(normalized_identifier)
            seen_identifiers.add(normalized_identifier)

        transfer_rule_map[transfer_subtype] = normalized_identifiers

    return transfer_rule_map    
def classify_transactions(xlsx_file,description_column_name,amount_values):


    invalid_amount_error = (
        "Unable to classify transactions because one or more "
        "amounts are missing or invalid."
    )

    
    if amount_values.empty or amount_values.isna().any():
        raise ValueError(invalid_amount_error)

    normalized_descriptions = xlsx_file[
        description_column_name
    ]

    normalized_descriptions = (
        normalized_descriptions
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    transfer_identifiers = (
        default_transfer_identifiers
        + user_transfer_identifiers
    )

    transfer_mask = pd.Series(
        False,
        index=xlsx_file.index
    )

    for transfer_identifier in transfer_identifiers:
        current_identifier_mask = (
            normalized_descriptions.str.contains(
                transfer_identifier,
                regex=False
            )
        )

        transfer_mask = (
            transfer_mask | current_identifier_mask
        )

    transaction_types = pd.Series(
        zero_amount_transaction_type,
        index=xlsx_file.index,
        dtype="object"
    )

    transaction_types.loc[
        transfer_mask
    ] = transfer_transaction_type

    transaction_types.loc[
        (amount_values > 0) & (~transfer_mask)
    ] = income_transaction_type

    transaction_types.loc[
        (amount_values < 0) & (~transfer_mask)
    ] = expense_transaction_type

    return transaction_types
def create_category_rule_map(user_category_identifiers):

    invalid_user_category_error = "User category identifiers must be provided as a dictionary."
    invalid_category_key_error = "Category section and category names must be text value."
    invalid_category_section_name_error = "User category identifiers contain an unsupported category."
    invalid__category_section_error = "Each category section must be provided as a dictionary."
    invalid_category_name_error = "User category identifiers contain an unsupported category."
    invalid_category_identifiers_error = "Category identifiers must be provided as a collection of text values."
    invalid_category_identifier_error = "Each category identifier must be a text value."

    user_identifier_key = "user identifiers"
    default_identifier_key = "default identifiers"


    default_category_identifiers = {
        income_transaction_type: {
            employment_income_category: [
                "payroll", "salary", "wages", "payroll deposit",
                "employer deposit", "adp payroll", "paychex"
            ],
            refund_reimbursement_category: [
                "refund", "reimbursement", "purchase return", "return credit",
                "merchant refund", "payment reversal", "cashback reward"
            ]
        },
        expense_transaction_type: {
            housing_category: [
                "rent payment", "mortgage payment", "property management",
                "homeowners association"
            ],
            utilities_category: [
                "electric bill", "water bill", "natural gas",
                "internet service", "cable service", "phone bill",
                "utility payment"
            ],
            healthcare_category: [
                "pharmacy", "medical center", "hospital", "urgent care",
                "dental", "dentist", "optometry", "vision care",
                "health insurance", "medical clinic"
            ],
            transportation_category: [
                "gas station", "fuel", "parking", "toll", "public transit",
                "rideshare", "uber", "lyft", "auto repair",
                "vehicle maintenance", "car insurance"
            ],
            groceries_category: [
                "grocery", "supermarket", "instacart", "kroger",
                "publix", "aldi", "whole foods", "trader joe"
            ],
            dining_category: [
                "restaurant", "cafe", "coffee shop", "fast food",
                "doordash", "uber eats", "grubhub", "food delivery"
            ],
            entertainment_category: [
                "movie theater", "cinema", "streaming service", "concert",
                "ticketmaster", "gaming", "amusement park", "netflix",
                "spotify"
            ],
            shopping_category: [
                "amazon", "walmart", "target", "ebay", "etsy",
                "department store", "clothing", "electronics",
                "online purchase"
            ]
        }
    } 

    valid_section_names =  {
        "income" : income_transaction_type,
        "expense": expense_transaction_type
    }

    valid_categories_by_section = {
        income_transaction_type: [
        employment_income_category,
        refund_reimbursement_category
    ],
    expense_transaction_type: [
        housing_category, utilities_category, healthcare_category,
        transportation_category, groceries_category,dining_category,
        entertainment_category,shopping_category
    ]
    }

    if user_category_identifiers is None:
        user_category_identifiers = {}

    elif not isinstance(user_category_identifiers,dict):
        raise TypeError(invalid_user_category_error)

    normalized_user_identifiers = {}

    for canonical_section_name, category_section in (default_category_identifiers.items()):
        normalized_user_identifiers[
            canonical_section_name
        ] = {}

        for canonical_category_name in category_section:
            normalized_user_identifiers[
                canonical_section_name
            ][
                canonical_category_name
            ] = []

    for section_name, category_section in (
    user_category_identifiers.items()
):
     if not isinstance(section_name, str):
        raise TypeError(invalid_category_key_error)

    normalized_section_name = (
        section_name
        .strip()
        .lower()
    )

    if normalized_section_name not in valid_section_names:
        raise ValueError(
            invalid_category_section_name_error
        )

    canonical_section_name = valid_section_names[
        normalized_section_name
    ]

    if not isinstance(category_section, dict):
        raise TypeError(
            invalid__category_section_error
        )

    for category_name, identifier_collection in (
        category_section.items()
    ):
        if not isinstance(category_name, str):
            raise TypeError(
                invalid_category_key_error
            )

        normalized_category_name = (
            category_name
            .strip()
            .lower()
        )

        canonical_category_name = None

        for approved_category_name in (
            valid_categories_by_section[
                canonical_section_name
            ]
        ):
            normalized_approved_category_name = (
                approved_category_name.lower()
            )

            if (
                normalized_category_name
                == normalized_approved_category_name
            ):
                canonical_category_name = (
                    approved_category_name
                )

                break

        if canonical_category_name is None:
            raise ValueError(
                invalid_category_name_error
            )

        if not isinstance(
            identifier_collection,
            (list, tuple, set)
        ):
            raise TypeError(
                invalid_category_identifiers_error
            )

        normalized_identifiers = (
            normalized_user_identifiers[
                canonical_section_name
            ][
                canonical_category_name
            ]
        )

        seen_identifiers = set(
            normalized_identifiers
        )

        for identifier in identifier_collection:
            if not isinstance(identifier, str):
                raise TypeError(
                    invalid_category_identifier_error
                )

            normalized_identifier = (
                identifier
                .strip()
                .lower()
            )

            if normalized_identifier == "":
                continue

            if normalized_identifier in seen_identifiers:
                continue

            normalized_identifiers.append(
                normalized_identifier
            )

            seen_identifiers.add(
                normalized_identifier
            )

    for canonical_section_name in normalized_user_identifiers:
        current_normalized_user_section = (
            normalized_user_identifiers[
                canonical_section_name
            ]
        )

        for canonical_category_name in (
            current_normalized_user_section
        ):
            current_normalized_user_section[
                canonical_category_name
            ].sort()

    category_rule_map = {}

    for (
        canonical_section_name,
        default_category_section
    ) in default_category_identifiers.items():

        category_rule_map[
            canonical_section_name
        ] = {}

        for (
            canonical_category_name,
            default_identifiers
        ) in default_category_section.items():

            user_identifiers = normalized_user_identifiers[
                canonical_section_name
            ][
                canonical_category_name
            ]

            category_rule_map[
                canonical_section_name
            ][
                canonical_category_name
            ] = {
                user_identifier_key: list(
                    user_identifiers
                ),
                default_identifier_key: list(
                    default_identifiers
                )
            }

    return category_rule_map
def categorize_transactions(xlsx_file,description_column_name,transaction_types,transfer_subtypes,category_rule_map):

    missing_description_column_error = "The transaction description column could not be found."
    misaligned_transaction_types_error = "Transaction types do not align with the statement transactions."
    misaligned_transfer_subtypes_error = "Transfer subtypes do not align with the statement transactions."
    invalid_category_rule_map_error = "Category rule map must be provided as a dictionary."
    incomplete_category_rule_map_error = "Category rule map must contain both Income and Expense rules."
    invalid_transaction_type_error = "Unable to categorize transaction because its transaction type is invalid."
    invalid_transfer_subtype_error = "Unable to categorize transaction because its transfer subtype is invalid."

    expense_categories = [
        housing_category,
        utilities_category,
        healthcare_category,
        transportation_category,
        groceries_category,
        dining_category,
        entertainment_category,
        shopping_category
    ]

    income_categories = [
       employment_income_category,
        refund_reimbursement_category
    ]

    user_identifier_key = "user identifiers"
    default_identifier_key = "default identifiers"
    user_identifier = 2
    default_identifier = 1
    incoming_transfers_category = "Incoming Transfers"
    outgoing_transfers_category = "Outgoing Transfers"


    if description_column_name not in xlsx_file.columns:
        raise ValueError( missing_description_column_error)

    if not transaction_types.index.equals(xlsx_file.index):
        raise ValueError(misaligned_transaction_types_error)

    if not transfer_subtypes.index.equals(xlsx_file.index):
        raise ValueError(misaligned_transfer_subtypes_error)

    if not isinstance(category_rule_map,dict):
        raise TypeError(invalid_category_rule_map_error)

    if (income_transaction_type not in category_rule_map or expense_transaction_type not in category_rule_map):
        raise ValueError(incomplete_category_rule_map_error)

    normalized_descriptions = xlsx_file[description_column_name]
    normalized_descriptions = normalized_descriptions.fillna("").astype(str).str.strip().str.lower()

    transaction_categories = pd.Series(pd.NA,index=xlsx_file.index, dtype = "object")

    for transaction_index in xlsx_file.index:

        transaction_type = transaction_types.loc[transaction_index]
        transfer_subtype = transfer_subtypes.loc[transaction_index]
        normalized_description = normalized_descriptions.loc[transaction_index]

        if transaction_type not in (income_transaction_type, expense_transaction_type, zero_amount_transaction_type):
            raise ValueError(invalid_transaction_type_error)
        
        if transfer_subtype not in (personal_transfer, owned_account_transfer, unclassified_transfer,not_a_transfer):
            raise ValueError(invalid_transfer_subtype_error) 


        if transaction_type == zero_amount_transaction_type:
            continue

        if transfer_subtype == owned_account_transfer:
            continue

        if transfer_subtype in (personal_transfer, unclassified_transfer):

             if transaction_type == income_transaction_type:
                transaction_categories.loc[
                    transaction_index
                    ] = incoming_transfers_category

             elif transaction_type == expense_transaction_type:
                    transaction_categories.loc[
                    transaction_index
                ] = outgoing_transfers_category 

             continue 

        if transaction_type == income_transaction_type:

                applicable_category_rules = category_rule_map[income_transaction_type]

                category_priority = income_categories
                fallback_category = other_income_category 

        else: 
            applicable_category_rules = category_rule_map[expense_transaction_type]

            category_priority = expense_categories
            fallback_category = other_expense_category

        if normalized_description == "":
                transaction_categories.loc[
                transaction_index
            ] = fallback_category

                continue 

        selected_category = pd.NA
        best_source_priority = 0
        best_identifier_length = 0

        for category_name in category_priority:

            category_rules = applicable_category_rules[
                category_name
            ]

            for identifier_source in (user_identifier_key, default_identifier_key):

                if identifier_source == user_identifier_key:
                    source_priority = user_identifier

                else:
                    source_priority = default_identifier

                identifiers = category_rules[identifier_source]

                for identifier in identifiers:

                    if  identifier in normalized_description:

                        identifier_length = len(identifier)

                        if source_priority > best_source_priority:
                            selected_category = category_name
                            best_source_priority = source_priority
                            best_identifier_length = identifier_length

                        elif (source_priority == best_source_priority and identifier_length > best_identifier_length):
                            selected_category = category_name
                            best_identifier_length = identifier_length

        if pd.notna(selected_category):

            transaction_categories.loc[
                transaction_index
            ] = selected_category

        else:
            transaction_categories.loc[
            transaction_index
        ] = fallback_category

    return transaction_categories        
def calculate_category_totals(amount_values,transaction_types,transaction_categories):
    
    invalid_amount_values_type_error = "Amount values must be provided as a pandas Series."
    invalid_transaction_types_error = "Transaction types must be provided as a pandas Series."
    invalid_transaction_categories_error = "Transaction categories must be provided as a pandas Series."
    misaligned_transaction_types_error = "Transaction types do not align with the transaction amounts."
    misaligned_transaction_categories_error = "Transaction categories do not align with the transaction amounts." 
    invalid_amount_values_error = "Unable to calculate category totals because one or more amounts are missing or invalid."
    invalid_transaction_type_error = "Unable to calculate category totals because a transaction type is invalid."
    amount_type_mismatch_error =  "A transaction amount does not match its transaction type."
    invalid_transaction_category_error = "A transaction category does not match its transaction type."

    income_categories = [
        employment_income_category,
        refund_reimbursement_category,
        incoming_transfers_category,
        other_income_category
    ]

    expense_categories = [
        housing_category,
        utilities_category,
        healthcare_category,
        transportation_category,
        groceries_category,
        dining_category,
        entertainment_category,
        shopping_category
        ]

    if not isinstance(amount_values,pd.Series):
        raise TypeError(invalid_amount_values_type_error)

    if not isinstance(transaction_types,pd.Series):
        raise TypeError(invalid_transaction_types_error)

    if not isinstance(transaction_categories,pd.Series):
        raise TypeError(invalid_transaction_categories_error)

    if transaction_types.Series.index.equals(amount_values.index):
        raise ValueError(misaligned_transaction_types_error)

    if transaction_categories.Series.index.equals(amount_values.index):
        raise ValueError(misaligned_transaction_categories_error)

    if amount_values.isna().any():
        raise ValueError(invalid_amount_values_error)

    if not pd.api.types.is_numeric_dtype(amount_values):
        raise ValueError(invalid_amount_values_error) 

    if amount_values == None:
        income_category_totals = pd.Series(dtype = "float")
        expense_category_totals = pd.Series(dtype = "float")
        return income_category_totals,expense_category_totals

    for transaction_index in amount_values.index():

        transaction_amount = amount_values[transaction_index]
        transaction_type = transaction_types[transaction_index]

        transaction_category = transaction_categories[transaction_index]

        if not transaction_type not in (income_transaction_type,expense_transaction_type,zero_amount_transaction_type):
            raise ValueError( invalid_transaction_type_error)

        if transaction_type is income_transaction_type:

            if transaction_amount < 0:
                raise ValueError(amount_type_mismatch_error)

            if transaction_category == None:
                continue

            if transaction_category not in income_transaction_type:
                raise ValueError (invalid_transaction_category_error)

            elif transaction_type in expense_transaction_type:

                if transaction_amount > 0:
                    raise ValueError(amount_type_mismatch_error)

                if transaction_category == None:
                    continue

                if not transaction_category in expense_categories:
                    raise ValueError(invalid_transaction_category_error)

            else:

                if not transaction_amount == 0:
                    raise ValueError(amount_type_mismatch_error)

                if not transaction_category == None:
                    raise ValueError(invalid_transaction_category_error)

            category_data = pd.DataFrame(amount = amount_values,transaction_type = transaction_types,transaction_category = transaction_categories)

            

    
def create_expense_category_pie_chart():
    pass
# ============================================================
# FINANCIAL CALCULATION FUNCTIONS
# ============================================================
def count_transactions(xlsx_file):

    transaction_count = len(xlsx_file)

    return transaction_count
def calculate_financial_summary(xlsx_file,description_column_name):

    transaction_count = count_transactions(xlsx_file)

    amount_column_name = identify_amount_column(xlsx_file)

    amount_values = xlsx_file[amount_column_name]

    amount_values = amount_values.astype(str)

    amount_values = amount_values.str.replace("$","",regex=False)

    amount_values = amount_values.str.replace(",","",regex=False)

    amount_values = pd.to_numeric(amount_values,errors="coerce")

    transaction_types = classify_transactions(xlsx_file,description_column_name,amount_values)

    income_amounts = amount_values[
        transaction_types == income_transaction_type
    ]

    expense_amounts = amount_values[
        transaction_types == expense_transaction_type
    ]

    total_income = income_amounts.sum()

    total_expenses = expense_amounts.sum()

    net_balance = (
        total_income + total_expenses
    )

    return (
        transaction_count,
        total_income,
        total_expenses,
        net_balance,
        amount_values,
        transaction_types
    )
def calculate_monthly_summary(
    xlsx_file,
    date_column_name,
    amount_values,
    transaction_types
):

    monthly_data = pd.DataFrame({
        "date": xlsx_file[date_column_name],
        "amount": amount_values,
        "transaction_type": transaction_types
    })

    monthly_data["date"] = pd.to_datetime(
        monthly_data["date"],
        errors="coerce"
    )

    monthly_data = monthly_data.dropna(
        subset=["date", "amount", "transaction_type"]
    )

    monthly_data["month"] = (
        monthly_data["date"].dt.month_name()
    )

    monthly_income = monthly_data[
        monthly_data["transaction_type"]
        == income_transaction_type
    ]

    monthly_expenses = monthly_data[
        monthly_data["transaction_type"]
        == expense_transaction_type
    ]

    monthly_income_totals = (
        monthly_income.groupby("month")["amount"].sum()
    )

    monthly_expense_totals = (
        monthly_expenses.groupby("month")["amount"].sum()
    )

    monthly_income_transaction_counts = (
        monthly_income.groupby("month").size()
    )

    monthly_expense_transaction_counts = (
        monthly_expenses.groupby("month").size()
    )

    monthly_transactions = (
        monthly_data.groupby("month").size()
    )

    months = monthly_transactions.index

    monthly_income_totals = (
        monthly_income_totals.reindex(
            months,
            fill_value=0
        )
    )

    monthly_expense_totals = (
        monthly_expense_totals.reindex(
            months,
            fill_value=0
        )
    )

    monthly_income_transaction_counts = (
        monthly_income_transaction_counts.reindex(
            months,
            fill_value=0
        )
    )

    monthly_expense_transaction_counts = (
        monthly_expense_transaction_counts.reindex(
            months,
            fill_value=0
        )
    )

    for month_name in months:

        if (
            monthly_income_transaction_counts.loc[
                month_name
            ] == 0
        ):
            raise ValueError(
                "Monthly transaction data is incomplete: "
                f"{month_name} has no income transactions."
            )

        if (
            monthly_expense_transaction_counts.loc[
                month_name
            ] == 0
        ):
            raise ValueError(
                "Monthly transaction data is incomplete: "
                f"{month_name} has no expense transactions."
            )

    months = months.tolist()

    income_totals = (
        monthly_income_totals.tolist()
    )

    expense_totals = (
        monthly_expense_totals.abs().tolist()
    )

    income_transaction_counts = (
        monthly_income_transaction_counts.tolist()
    )

    expense_transaction_counts = (
        monthly_expense_transaction_counts.tolist()
    )

    return (
        months,
        income_totals,
        expense_totals,
        income_transaction_counts,
        expense_transaction_counts
    )
def calculate_monthly_transfer_summary(xlsx_file,date_column_name,amount_values,transaction_types,category_rule_map):
    pass

def calculate_expense_category_summary(
    amount_values,
    transaction_types,
    transaction_categories
):
    pass
def calculate_income_category_summary(
    amount_values,
    transaction_types,
    transaction_categories
):
    pass
# ============================================================
# AI FINANCIAL INSIGHT FUNCTIONS
# ============================================================
def prepare_financial_insight_data(
    financial_summary,
    monthly_summary,
    transfer_summary
):
    pass

def generate_financial_insights(
    financial_insight_data
):
    pass

def validate_financial_insights(
    financial_insights
):
    pass
# ============================================================
# FINANCIAL HEALTH  FUNCTIONS
# ============================================================
def determine_financial_health(total_income, total_expenses):

    # SET the savings-rate thresholds
    very_healthy_threshold = 20
    healthy_threshold = 10
    needs_attention_threshold = 5
    caution_threshold = 0
    weak_threshold = -10
    very_weak_threshold = -25
    

    # SET the invalid-income error message
    invalid_total_income_error = "Total income cannot be less than zero."

    if total_income < 0:
        raise ValueError(invalid_total_income_error)

    normalized_expenses = abs(total_expenses)

    if total_income == 0:

        savings_rate = None

        if normalized_expenses == 0:
            financial_health = unable_to_determine_status

        else:
            financial_health = very_weak_status

        return financial_health, savings_rate

    calculated_net_balance = total_income - normalized_expenses

    savings_rate = (
        calculated_net_balance / total_income
    ) * 100

    if savings_rate >= very_healthy_threshold:
        financial_health = very_healthy_status

    elif savings_rate >= healthy_threshold:
        financial_health = healthy_status

    elif savings_rate >= needs_attention_threshold:
        financial_health = needs_attention_status

    elif savings_rate >= caution_threshold:
        financial_health = caution_status

    elif savings_rate >= weak_threshold:
        financial_health = weak_status

    elif savings_rate >= very_weak_threshold:
        financial_health = very_weak_status

    else:
        financial_health =at_risk_status 

    return financial_health, savings_rate
def get_financial_health_colors(financial_health):

    health_color_map = {
        very_healthy_status: ("#006400", "#E8F5E9"),
        healthy_status: ("#228B22", "#EEF8EE"),
        needs_attention_status: ("#6B8E23", "#F4F8E8"),
        caution_status: ("#B8860B", "#FFF8DC"),
        weak_status: ("#FFB000", "#FFF4CC"),
        at_risk_status: ("#FF4500", "#FFF0EB"),
        very_weak_status: ("#8B0000", "#FDECEC"),
        unable_to_determine_status: ("#666666", "#F2F2F2")
}
    default_colors = ("#666666", "#F2F2F2")

    selected_colors = health_color_map.get(
        financial_health,
        default_colors
    )
    (
        status_forground_color,
        status_background_color
    ) = selected_colors

    return status_forground_color, status_background_color   
def create_financial_health_summary(financial_health_axis,financial_health,savings_rate):
    
    financial_health_title = "Financial Health"
    status_label = "Status:"
    savings_rate_label = "Savings Rate:"
    unavailable_rate_text = "N/A"

    card_x_position = 0.01
    card_y_position = 0.45
    card_width = .98
    card_height = .8

    common_vertical_position = .80
    title_horizontal_position = .16
    status_label_horizontal_position = .41
    savings_label_horizontal_position = .74
    savings_result_horizontal_position = .75

    title_font_size = 13
    label_font_size = 11
    result_font_size = 11

    card_border_width = 1.5
    corner_rounding_size = .03

    financial_health_axis.axis("off")

    (
    status_foreground_color,
    status_background_color
    ) = get_financial_health_colors(financial_health)

    if savings_rate == None:
        formatted_saving_rate = unavailable_rate_text
    else:
       formatted_saving_rate = f"{savings_rate:.2f}%"

    status_text = financial_health
    savings_rate_text = formatted_saving_rate

    financial_health_card = FancyBboxPatch(
    (card_x_position, card_y_position),
    card_width,
    card_height,
    transform=financial_health_axis.transAxes,
    boxstyle=(
        f"round,pad=0.02,"
        f"rounding_size={corner_rounding_size}"
    ),
    facecolor=status_background_color,
    edgecolor=status_foreground_color,
    linewidth=card_border_width,
    clip_on=False,
    zorder=0
)
    financial_health_axis.add_patch(financial_health_card)

    financial_health_axis.text(
        title_horizontal_position,
        common_vertical_position,
        financial_health_title,
        transform=financial_health_axis.transAxes,
        ha="center",
        va="center",
        fontsize=title_font_size,
        fontweight="bold",
        color=status_foreground_color,
        zorder=1
    )
    
    financial_health_axis.text(
        status_label_horizontal_position,
        common_vertical_position,
        status_label,
        transform=financial_health_axis.transAxes,
        ha="right",
        va="center",
        fontsize=label_font_size,
        fontweight="normal",
        color="black",
        zorder=1
    )

    financial_health_axis.text(
        status_label_horizontal_position,
        common_vertical_position,
        status_text,
        transform=financial_health_axis.transAxes,
        ha="left",
        va="center",
        fontsize=result_font_size,
        fontweight="bold",
        color=status_foreground_color,
        zorder=1
    )

    financial_health_axis.text(
        savings_label_horizontal_position,
        common_vertical_position,
        savings_rate_label,
        transform=financial_health_axis.transAxes,
        ha="right",
        va="center",
        fontsize=label_font_size,
        fontweight="normal",
        color="black",
        zorder=1
    )

    financial_health_axis.text(
        savings_result_horizontal_position,
        common_vertical_position,
        savings_rate_text,
        transform=financial_health_axis.transAxes,
        ha="left",
        va="center",
        fontsize=result_font_size,
        fontweight="bold",
        color=status_foreground_color,
        zorder=1
    )

    return None   
# ============================================================
# TABLE STYLING FUNCTIONS
# ============================================================
def style_financial_table(financial_table):

   fin_tab = financial_table.get_celld()

   for (row, column), cell in fin_tab.items():

        if row == 0:
            header_cell = cell
            header_cell.set_facecolor("darkblue")
            header_cell.set_text_props(
                color="white",
                weight="bold",
                fontsize=12,
                ha="center",
                va="center"
            )
            header_cell.set_edgecolor("white")
            header_cell.set_linewidth(1.0)

        else:
            data_cell = cell

            if row % 2 == 0:
                data_cell.set_facecolor("whitesmoke")
            else:
                data_cell.set_facecolor("white")

            data_cell.set_text_props(
                fontsize=10,
                ha="center",
                va="center"
            )
            data_cell.set_edgecolor("lightgray")
            data_cell.set_linewidth(0.8)

   financial_table.scale(1.0, 2.0)

   return None
# ============================================================
# INCOME AND EXPENSE CHART FUNCTIONS
# ============================================================
def create_monthly_income_expenses_chart(
        income_axis,
        months,
        income_totals,
        expense_totals
):

    # SET the width of each bar
    bar_width = 0.15

    # SET the positions of the bars on the x-axis
    bar_gap = 0.07  
    
    # CALCULATE the x-axis positions for each month
    x_positions = np.arange(len(months))

    income_positions = x_positions - ((bar_width + bar_gap) / 2)
    expense_positions = x_positions + ((bar_width + bar_gap) / 2)

    income_bars = income_axis.bar(
        income_positions,
        income_totals,
        width=bar_width,
        label="Income",
        color="limegreen",
        alpha = 1.0,
        zorder = 2   
        )

    expense_bars = income_axis.bar(
        expense_positions,
        expense_totals,
        width=bar_width,
        label="Expenses",
        color="red",
        alpha = 1.0,
        zorder = 2
    )

    income_axis.set_xticks(x_positions)
    income_axis.set_xticklabels(months)

    income_axis.set_xlabel("Month")
    income_axis.set_ylabel("Amount ($)")
    income_axis.set_title("MONTHLY INCOME vs EXPENSES",fontsize=15, fontweight="bold", color="black")

    income_axis.spines["top"].set_visible(False)
    income_axis.spines["right"].set_visible(False)

    income_axis.yaxis.grid(
        True,
        linestyle="--",
        alpha = 1.0,
        color = "lightgrey",
        zorder = 2
    )

    income_axis.legend(loc = "lower center",bbox_to_anchor=(0.1, -0.35),
    ncol=1,fontsize=11,frameon=False, columnspacing = 5)
    
    return income_bars, expense_bars
def style_monthly_income_expenses_chart(income_axis, income_bars, expense_bars):

    current_ylim, current_ymax = income_axis.get_ylim()

    label_offset_percentage = 0.02
    y_axis_expansion_percentage = 0.08
    expansion_amount = current_ymax * y_axis_expansion_percentage
    new_ymax = current_ymax + expansion_amount

    label_offset = current_ymax * label_offset_percentage

    for income_bar in income_bars:
        bar_height = income_bar.get_height()
        bar_center = (income_bar.get_x() + income_bar.get_width() / 2)
        formatted_value = f"${bar_height:,.0f}"
        income_axis.text(
            bar_center,
            bar_height + label_offset,
            formatted_value,
            ha="center",
            va="bottom",
            fontsize=9,
            color="black"
        )
        
    for expense_bar in expense_bars:
        bar_height = expense_bar.get_height()
        bar_center = (expense_bar.get_x() + expense_bar.get_width() / 2)
        formatted_value = f"${bar_height:,.0f}"
        income_axis.text(
            bar_center,
            bar_height + label_offset,
            formatted_value,
            ha="center",
            va="bottom",
            fontsize=9,
            color="black"
        )
    
    income_axis.set_ylim(current_ylim, new_ymax)

    card = FancyBboxPatch(
        (-0.15, -0.32),
        1.17,
        1.47,
        transform=income_axis.transAxes,
        boxstyle="round,pad=0.02,rounding_size=0.03",
        facecolor="white",
        edgecolor="lightblue",
        linewidth=1.5,
        clip_on=False,
        zorder=-1
)

    income_axis.add_patch(card)  
# ============================================================
# TRANSACTION-COUNT CHART FUNCTIONS
# ============================================================
def create_monthly_income_expense_transaction_chart(transaction_axis,months,income_transaction_counts,
    expense_transaction_counts):

    # CALCULATE the x-axis positions for each month

    x_positions = np.arange(len(months))

    bar_width = 0.15
    bar_gap = 0.07

    income_transaction_positions = (x_positions - ((bar_width + bar_gap) / 2))
    expense_transaction_positions = (x_positions + ((bar_width + bar_gap) / 2))

    income_transaction_bars = transaction_axis.bar(
        income_transaction_positions,
        income_transaction_counts,
        width=bar_width,
        color="limegreen",
        alpha=1.0,
        zorder=2,
        label="Income"
    )

    expense_transaction_bars = transaction_axis.bar(
        expense_transaction_positions,
        expense_transaction_counts,
        width=bar_width,
        color="red",
        alpha=1.0,
        zorder=2,
        label="Expenses"
    )

    transaction_axis.set_xticks(x_positions)
    transaction_axis.set_xticklabels(months)

    transaction_axis.set_xlabel("Month")
    transaction_axis.set_ylabel("Transactions")
    transaction_axis.set_title("INCOME vs EXPENSE TRANSACTIONS",fontsize=15, fontweight="bold", color="black")

    transaction_axis.legend(loc = "lower center",bbox_to_anchor=(0.1, -0.35),
        ncol=1,fontsize=11,frameon=False, columnspacing = 5)

    return income_transaction_bars, expense_transaction_bars
def style_monthly_income_expense_transaction_chart(transaction_axis,income_transaction_bars,
    expense_transaction_bars):

    label_offset_percentage = 0.02
    y_axis_expansion = 0.08

    current_ymin, current_ymax = (transaction_axis.get_ylim())

    expansion_amount = (current_ymax * y_axis_expansion)

    new_ymax = (current_ymax + expansion_amount)

    label_offset = (current_ymax * label_offset_percentage)

    all_transaction_bars = (
        list(income_transaction_bars)
        + list(expense_transaction_bars)
    )

    for transaction_bar in all_transaction_bars:
        bar_height = transaction_bar.get_height()

        bar_center = (
            transaction_bar.get_x()
            + transaction_bar.get_width() / 2
        )

        formatted_count = f"{bar_height:,.0f}"

        transaction_axis.text(
            bar_center,
            bar_height + label_offset,
            formatted_count,
            ha="center",
            va="bottom",
            fontsize=9,
            color="black"
        )

    transaction_axis.set_ylim(
        current_ymin,
        new_ymax
    )

    transaction_axis.yaxis.grid(
        True,
        linestyle="--",
        color="grey",
        alpha=0.3
    )

    transaction_axis.spines[
        "top"
    ].set_visible(False)

    transaction_axis.spines[
        "right"
    ].set_visible(False)

    card = FancyBboxPatch(
        (-0.15, -0.32),
        1.17,
        1.47,
        transform=transaction_axis.transAxes,
        boxstyle=(
            "round,pad=0.02,"
            "rounding_size=0.03"
        ),
        facecolor="white",
        edgecolor="lightblue",
        linewidth=1.5,
        clip_on=False,
        zorder=-1
    )

    transaction_axis.add_patch(card)

    return None
# ============================================================
# TRANSFER CHART FUNCTIONS
# ============================================================
def create_monthly_transfer_chart(
    transfer_axis,
    months,
    transfer_totals,
    transfer_counts
):
    pass

def style_monthly_transfer_chart(
    transfer_axis,
    transfer_total_bars,
    transfer_count_bars
):
    pass
# ============================================================
# SHARED CHART STYLING FUNCTIONS
# ============================================================
def round_bar_tops(chart_axis, bars,):

    vertical_radius_percentage = 0.02
    horizontal_radius_percentage = 0.25
    current_y_min, current_y_max = chart_axis.get_ylim()

    y_axis_range = current_y_max - current_y_min

    for bar in bars:

        bar_x = bar.get_x()
        bar_y = bar.get_y()
        bar_width = bar.get_width()
        bar_height = bar.get_height()

        if bar_height <= 0:
            continue

        horizontal_radius = (
            bar_width * horizontal_radius_percentage
        )

        calculated_vertical_radius = (
            y_axis_range * vertical_radius_percentage
        )

        maximum_vertical_radius = bar_height / 2

        if calculated_vertical_radius < maximum_vertical_radius:
            vertical_radius = calculated_vertical_radius
        else:
            vertical_radius = maximum_vertical_radius

        bar_color = bar.get_facecolor()
        bar_zorder = bar.get_zorder()

        path_vertices = [
            (bar_x, bar_y),

            (
                bar_x,
                bar_y + bar_height - vertical_radius
            ),

            (
                bar_x,
                bar_y + bar_height
            ),

            (
                bar_x + horizontal_radius,
                bar_y + bar_height
            ),

            (
                bar_x + bar_width - horizontal_radius,
                bar_y + bar_height
            ),

            (
                bar_x + bar_width,
                bar_y + bar_height
            ),

            (
                bar_x + bar_width,
                bar_y + bar_height - vertical_radius
            ),

            (
                bar_x + bar_width,
                bar_y
            ),

            (
                bar_x,
                bar_y
            ),

            (
                bar_x,
                bar_y
            )
        ]

        path_codes = [
            MplPath.MOVETO,
            MplPath.LINETO,
            MplPath.CURVE3,
            MplPath.CURVE3,
            MplPath.LINETO,
            MplPath.CURVE3,
            MplPath.CURVE3,
            MplPath.LINETO,
            MplPath.LINETO,
            MplPath.CLOSEPOLY
        ]

        rounded_bar_path = MplPath(
            path_vertices,
            path_codes
        )

        rounded_bar = PathPatch(
            rounded_bar_path,
            facecolor=bar_color,
            edgecolor="none",
            zorder=bar_zorder
        )

        bar.set_visible(False)

        chart_axis.add_patch(
            rounded_bar
        )

    return None
# ============================================================
# REPORT CREATION FUNCTIONS
# ============================================================
def create_financial_report(
    transaction_count,
    start_date,
    end_date,
    total_income,
    total_expenses,
    net_balance,
    months,
    income_totals,
    expense_totals,
    income_transaction_counts,
    expense_transaction_counts
):

    financial_health, savings_rate = determine_financial_health(
        total_income,
        total_expenses
    )

    # Create report

    report_figure = plt.figure(figsize=(14, 8))

    formatted_start_date = start_date.strftime("%B %d, %Y")
    formatted_end_date = end_date.strftime("%B %d, %Y")

    report_period = (
        f"Reporting Period: "
        f"{formatted_start_date} - {formatted_end_date}"
    )

    report_figure.suptitle(
        program_title,
        fontsize=23,
        fontweight="bold",
        color="Black"
    )

    report_figure.text(
        0.5,
        0.9,
        report_period,
        ha="center",
        fontsize=15
    )

    report_layout = report_figure.add_gridspec(
        4,
        2,
        height_ratios=[0.2, 1.0, 0.35, 1.6]
    )

    banner_axis = report_figure.add_subplot(
        report_layout[0, :]
    )

    financial_summary = report_figure.add_subplot(
        report_layout[1, :]
    )

    financial_health_axis = report_figure.add_subplot(
        report_layout[2, :]
    )

    income_axis = report_figure.add_subplot(
        report_layout[3, 0]
    )

    transaction_axis = report_figure.add_subplot(
        report_layout[3, 1]
    )

    financial_summary.axis("off")

    banner_axis.set_facecolor(
        "darkblue"
    )

    banner_axis.set_xticks([])
    banner_axis.set_yticks([])

    banner_axis.text(
        0.5,
        0.5,
        "Financial Summary",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="white"
    )

    financial_summary_data = [
        ["Transactions", transaction_count],
        ["Total Income", f"${total_income:,.2f}"],
        ["Total Expenses", f"${total_expenses:,.2f}"],
        ["Net Balance", f"${net_balance:,.2f}"]
    ]

    financial_table = financial_summary.table(
        cellText=financial_summary_data,
        colLabels=["Category", "Amount"],
        loc="center"
    )

    style_financial_table(
        financial_table
    )

    create_financial_health_summary(
        financial_health_axis,
        financial_health,
        savings_rate
    )

    income_bars, expense_bars = (
        create_monthly_income_expenses_chart(
            income_axis,
            months,
            income_totals,
            expense_totals
        )
    )

    style_monthly_income_expenses_chart(
        income_axis,
        income_bars,
        expense_bars
    )

    (
        income_transaction_bars,
        expense_transaction_bars
    ) = create_monthly_income_expense_transaction_chart(
        transaction_axis,
        months,
        income_transaction_counts,
        expense_transaction_counts
    )

    style_monthly_income_expense_transaction_chart(
        transaction_axis,
        income_transaction_bars,
        expense_transaction_bars
    )

    round_bar_tops(
        income_axis,
        income_bars
    )

    round_bar_tops(
        income_axis,
        expense_bars
    )

    round_bar_tops(
        transaction_axis,
        income_transaction_bars
    )

    round_bar_tops(
        transaction_axis,
        expense_transaction_bars
    )

    report_figure.subplots_adjust(
        top=0.84,
        bottom=0.18,
        hspace=0.20,
        wspace=0.30
    )

    plt.show()

    return report_figure

def create_financial_insights_summary(
    financial_insights_axis,
    financial_insights
):
    pass
# ============================================================
# REPORT EXPORT FUNCTIONS
# ============================================================
def save_financial_report(report_figure):

    chart_prompt = "Would you like to save this chart as an image? (Y/N): "
    invalid_save_choice_message = "The input is invalid."
    chart_saved_successfully_message = "Charts have been saved successfully."
    none_error = "Must Enter A Valid Input."
    file_name_prompt = "Please Enter The File Name: "

    while True:

        save_choice = input(chart_prompt)

        if save_choice.upper() == "Y":

            while True:

                file_name = input(file_name_prompt)
                file_name = file_name.strip()

                if file_name == "":
                    print(none_error)
                    continue

                else:
                    financial_report_file_name = (
                        file_name + "_financial_report.png"
                    )

                    report_figure.savefig(
                        financial_report_file_name
                    )

                    print(
                        chart_saved_successfully_message
                    )

                    return

        elif save_choice.upper() == "N":
            break

        else:
            print(
                invalid_save_choice_message
            )

    return
def export_financial_data(
    combined_transactions,
    financial_summary,
    monthly_summary,
    transfer_summary
):
    pass
# ============================================================
# MAIN
# ============================================================
def main():

    display_welcome_screen()

    selected_file = select_xlsx_file()

    if selected_file is None:
        print(no_file_selected_error)
        return

    try:
        xlsx_path = validate_xlsx_file(selected_file)

        xlsx_file = open_xlsx(xlsx_path)

        if xlsx_file is None:
            return

        date_column_name = identify_date_column(
    xlsx_file
        )

        description_column_name = identify_description_column(
            xlsx_file
        )

        start_date, end_date = determine_date_range(
            xlsx_file,
            date_column_name
        )

        (
            transaction_count,
            total_income,
            total_expenses,
            net_balance,
            amount_values,
            transaction_types
        ) = calculate_financial_summary(
            xlsx_file,
            description_column_name
        )

        (
            months,
            income_totals,
            expense_totals,
            income_transaction_counts,
            expense_transaction_counts
        ) = calculate_monthly_summary(
            xlsx_file,
            date_column_name,
            amount_values,
            transaction_types
        )

        report_figure = create_financial_report(
            transaction_count,
            start_date,
            end_date,
            total_income,
            total_expenses,
            net_balance,
            months,
            income_totals,
            expense_totals,
            income_transaction_counts,
            expense_transaction_counts
        )

        save_financial_report(report_figure,)

    except Exception as error:
        print(error)

if __name__ == "__main__":
    main()