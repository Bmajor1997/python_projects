# Project Name: Personal Spending Analyzer
# ============================================================
# IMPORTS
# ============================================================
import pandas as pd
from pandas.api.types import is_numeric_dtype
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, PathPatch, Rectangle
from pathlib import Path
from matplotlib.path import Path as MplPath
from pathlib import Path
from tkinter import filedialog
import tkinter as tk
import numpy as np
from openai import Openai
from pydantic import BaseModel
import os
import json
# ============================================================
# APPLICATION INFORMATIONS
# ============================================================
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
incoming_transfers_category = "Incoming Transfers"
outgoing_transfers_category = "Outgoing Transfers"
# ============================================================
# DISPLAY FUNCTIONS
# ============================================================
def display_welcome_screen():

    """Display the program title, version, and welcome message."""

    # Display the application header.
    print(divider)
    print(program_title)
    print(divider)

    # Display the welcome message.
    print(welcome_message)
    print(divider)
# ============================================================
# FILE SELECTION AND VALIDATION FUNCTIONS
# ============================================================
def select_xlsx_file():

    """Open a file dialog and return the path of the selected XLSX file."""

    # Create and hide the main Tkinter window.
    root = tk.Tk()
    root.withdraw()

    # Open the file dialog and restrict the available file type to XLSX.
    selected_file = filedialog.askopenfilename(
        title=file_dialog_title,
        filetypes=xlsx_file_types
    )

    # Close the hidden Tkinter window after the dialog is finished.
    root.destroy()

    # Return None when the user closes the dialog without selecting a file.
    if not selected_file:
        return None

    # Return the path of the selected XLSX file.
    return selected_file

def validate_xlsx_file(selected_file):
    
    """Validate the selected XLSX file and return its Path object."""

    # Convert the selected file path into a Path object.
    xlsx_path = Path(selected_file)

    # Confirm that the selected file exists.
    if not xlsx_path.exists():
        raise Exception(no_file_selected_error)

    # Confirm that the selected file uses the XLSX extension.
    if xlsx_path.suffix != ".xlsx":
        raise Exception(invalid_file_type_error)

    # Confirm that the selected file contains data.
    if xlsx_path.stat().st_size == 0:
        raise Exception(empty_file_error)

    # Return the validated XLSX file path.
    return xlsx_path

def open_xlsx(xlsx_path):

    """Open an XLSX file and return its contents as a pandas DataFrame."""

    # Attempt to read the XLSX file into a pandas DataFrame.
    try:
        xlsx_file = pd.read_excel(xlsx_path)

    # Display a user-friendly message if the file cannot be opened.
    except Exception:
        print(xlsx_open_error)
        return None

    # Return the successfully loaded XLSX data.
    return xlsx_file

def select_xlsx_files():

    """Open a file dialog and return the selected XLSX file paths."""

    # Create and hide the main Tkinter window.
    root = tk.Tk()
    root.withdraw()

    # Open the file dialog and allow the user to select
    # one or more XLSX bank statements.
    selected_files = filedialog.askopenfilenames(
        title="Select Your Bank XLSX Files",
        filetypes=xlsx_file_types
    )

    # Close the hidden Tkinter window after the dialog is finished.
    root.destroy()

    # Return None when the user closes the dialog
    # without selecting any files.
    if not selected_files:
        return None

    # Convert the Tkinter tuple into a list for downstream processing.
    return list(selected_files)

def combine_xlsx_files(selected_files):

    """
    Validate, open, standardize, and combine multiple bank statements.

    Each statement is reduced to the transaction columns required by the
    Financial Analyzer and those columns are standardized before the
    statements are concatenated.
    """

    # Confirm that the selected files are stored in a supported collection.
    if not isinstance(selected_files, (list, tuple)):
        raise TypeError(
            "Selected bank statements must be provided as a collection."
        )

    # Confirm that at least one statement was supplied.
    if len(selected_files) == 0:
        raise ValueError(
            "At least one bank statement must be selected."
        )

    # Store each prepared statement before they are combined.
    prepared_statements = []

    # Process every selected bank statement.
    for selected_file in selected_files:

        # Validate the current XLSX file using the project's
        # existing file validation function.
        xlsx_path = validate_xlsx_file(
            selected_file
        )

        # Open the validated bank statement.
        statement_data = open_xlsx(
            xlsx_path
        )

        # Stop processing when the statement could not be opened.
        if statement_data is None:
            raise ValueError(
                f"Could not open bank statement: {xlsx_path.name}"
            )

        # Confirm that the statement contains transaction rows.
        if statement_data.empty:
            raise ValueError(
                f"Bank statement contains no transaction rows: "
                f"{xlsx_path.name}"
            )

        # Identify the transaction columns using the project's
        # existing column-identification functions.
        date_column_name = identify_date_column(
            statement_data
        )

        description_column_name = (
            identify_description_column(
                statement_data
            )
        )

        amount_column_name = identify_amount_column(
            statement_data
        )

        # Confirm that the statement contains at least one
        # usable transaction date.
        determine_date_range(
            statement_data,
            date_column_name
        )

        # Retrieve only the columns required by the existing
        # Financial Analyzer.
        prepared_statement = statement_data[
            [
                date_column_name,
                description_column_name,
                amount_column_name
            ]
        ].copy()

        # Standardize the required transaction column names.
        # This allows statements from different banks to be
        # combined even when their original headers differ.
        prepared_statement = prepared_statement.rename(
            columns={
                date_column_name: "Date",
                description_column_name: "Description",
                amount_column_name: "Amount"
            }
        )

        # Store the prepared statement.
        prepared_statements.append(
            prepared_statement
        )

    # Combine every prepared bank statement into one transaction dataset.
    combined_statement = pd.concat(
        prepared_statements,
        ignore_index=True
    )

    # Confirm that transactions remain after the statements are combined.
    if combined_statement.empty:
        raise ValueError(
            "The combined bank statements contain no transactions."
        )

    # Create temporary datetime values so statements can be placed
    # into chronological transaction order.
    transaction_dates = pd.to_datetime(
        combined_statement["Date"],
        errors="coerce"
    )

    # Sort the combined transactions chronologically while preserving
    # rows whose dates could not be converted.
    combined_statement = (
        combined_statement
        .assign(_transaction_date_sort=transaction_dates)
        .sort_values(
            "_transaction_date_sort",
            na_position="last"
        )
        .drop(
            columns="_transaction_date_sort"
        )
        .reset_index(
            drop=True
        )
    )

    # Return one DataFrame representing all selected statements.
    return combined_statement

def prepare_combined_statement(combined_statement):

    """
    Prepare the combined bank-statement DataFrame for the existing
    Financial Analyzer calculations.
    """

    # Confirm that the combined statement is a pandas DataFrame.
    if not isinstance(combined_statement, pd.DataFrame):
        raise TypeError(
            "Combined statement data must be provided as a pandas DataFrame."
        )

    # Confirm that the combined statement contains transactions.
    if combined_statement.empty:
        raise ValueError(
            "The combined bank statement contains no transactions."
        )

    # Retrieve the standardized date column.
    date_column_name = identify_date_column(
        combined_statement
    )

    # Retrieve the standardized description column.
    description_column_name = (
        identify_description_column(
            combined_statement
        )
    )

    # Confirm that a supported amount column exists.
    identify_amount_column(
        combined_statement
    )

    # Determine the complete reporting period across
    # every selected bank statement.
    start_date, end_date = determine_date_range(
        combined_statement,
        date_column_name
    )

    # Return the information required by the existing analysis workflow.
    return (
        date_column_name,
        description_column_name,
        start_date,
        end_date
    )
# ============================================================
# COLUMN IDENTIFICATION FUNCTIONS
# ============================================================
def identify_date_column(xlsx_file):

    """Identify and return the original name of the statement's date column."""

    # Define the column names that may represent transaction dates.
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

    # Define the error displayed when no supported date column is found.
    no_date_column_found_error = "No Date Column Found."

    # Normalize the statement's column names for consistent comparison.
    normalized_columns = xlsx_file.columns.str.strip().str.lower()

    # Convert the supported date column names into a pandas Index.
    possible_date_columns = pd.Index(possible_date_column_names)

    # Find supported date column names within the statement.
    matching_columns = normalized_columns.intersection(
        possible_date_columns
    )

    # Stop the analysis when the statement has no supported date column.
    if len(matching_columns) == 0:
        raise ValueError(no_date_column_found_error)

    # Select the first supported date column that was found.
    matching_column_name = matching_columns[0]

    # Locate the matching column's position in the statement.
    column_position = normalized_columns.get_loc(
        matching_column_name
    )

    # Retrieve the column's original name before normalization.
    date_column_name = xlsx_file.columns[column_position]

    # Return the original date column name.
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

    """Identify and return the original name of the statement's amount column."""

    # Define the column names that may represent transaction amounts.
    possible_amount_column_names = [
        "amount",
        "transaction amount",
        "transaction_amount",
        "value",
        "transaction value",
        "payment amount"
    ]

    # Define the error displayed when no supported amount column is found.
    no_amount_column_found_error = "Could not find Amount column"

    # Normalize the statement's column names for consistent comparison.
    normalized_columns = xlsx_file.columns.str.strip().str.lower()

    # Convert the supported amount column names into a pandas Index.
    possible_amount_columns = pd.Index(possible_amount_column_names)

    # Find supported amount column names within the statement.
    matching_amount = normalized_columns.intersection(
        possible_amount_columns
    )

    # Stop the analysis when the statement has no supported amount column.
    if len(matching_amount) == 0:
        raise ValueError(no_amount_column_found_error)

    # Select the first supported amount column that was found.
    matching_column_name = matching_amount[0]

    # Locate the matching column's position in the statement.
    column_position = normalized_columns.get_loc(
        matching_column_name
    )

    # Retrieve the column's original name before normalization.
    amount_column_name = xlsx_file.columns[column_position]

    # Return the original amount column name.
    return amount_column_name

def identify_description_column(xlsx_file):

    """Identify and return the original name of the transaction description column."""

    # Define the column names that may contain transaction descriptions.
    possible_description_column_names = [
        "description",
        "details"
    ]

    # Define the error displayed when no supported description column is found.
    missing_description_column = (
        "Could not find transaction description column"
    )

    # Normalize the statement's column names for consistent comparison.
    normalized_columns = xlsx_file.columns.str.strip().str.lower()

    # Find supported description column names within the statement.
    matching_columns = normalized_columns.intersection(
        pd.Index(possible_description_column_names)
    )

    # Stop the analysis when no supported description column is found.
    if matching_columns.empty:
        raise ValueError(missing_description_column)

    # Select the first supported description column that was found.
    matching_column_name = matching_columns[0]

    # Locate the matching column's position in the statement.
    column_position = normalized_columns.get_loc(
        matching_column_name
    )

    # Retrieve the column's original name before normalization.
    description_column_name = xlsx_file.columns[column_position]

    # Return the original description column name.
    return description_column_name
# ============================================================
# TRANSACTION CLASSIFICATION FUNCTIONS
# ============================================================
def create_transfer_rule_map(user_owned_account_identifiers):

    """Create and return normalized identifier rules for transfer subtypes."""

    # Define the error displayed for an invalid identifier collection or value.
    invalid_owned_account_error = "Owned account must be provided as a collection of text values."
    

    # Use an empty collection when no owned-account identifiers are provided.
    if user_owned_account_identifiers is None:
        user_owned_account_identifiers = []

    # Confirm that the owned-account identifiers are stored in a collection.
    elif not isinstance(user_owned_account_identifiers,(list, tuple, set)):
        raise TypeError(invalid_owned_account_error)

    # Store the user-provided owned-account identifiers.
    owned_account_values = user_owned_account_identifiers

    # Define identifiers commonly associated with personal transfers.
    default_personal_transfer_identifiers = {
        "zel to",
        "zel from",
        "zelle to",
        "zelle from",
        "venmo",
        "cash app",
        "cash app payment"
    }

    # Define general identifiers for transfers without a known subtype.
    default_unclassified_transfer_identifiers = {
        "transfer",
        "transfer funds",
        "ach transfer"
    }

    # Associate each transfer subtype with its identifier collection.
    transfer_rule_sources = {
        "Personal transfer identifiers": default_personal_transfer_identifiers,
        "Unclassified transfer identifiers": default_unclassified_transfer_identifiers,
        "Owned account transfer": owned_account_values
    }

    # Create the dictionary that will contain the normalized transfer rules.
    transfer_rule_map = {}

    # Process the identifiers belonging to each transfer subtype.
    for transfer_subtype, identifiers in transfer_rule_sources.items():

        # Create containers for normalized values and duplicate tracking.
        normalized_identifiers = []
        seen_identifiers = set()

        # Normalize and validate each identifier.
        for identifier in identifiers:

            # Confirm that every identifier is a text value.
            if not isinstance(identifier, str):
                raise TypeError(invalid_owned_account_error)

            # Remove surrounding spaces and convert the identifier to lowercase.
            normalized_identifier = identifier.strip().lower()

            # Ignore identifiers that are empty after normalization.
            if not normalized_identifier:
                continue

            # Ignore identifiers that have already been added.
            if normalized_identifier in seen_identifiers:
                continue

            # Store the normalized identifier and mark it as processed.
            normalized_identifiers.append(normalized_identifier)
            seen_identifiers.add(normalized_identifier)

        # Associate the normalized identifiers with their transfer subtype.
        transfer_rule_map[transfer_subtype] = normalized_identifiers

    # Return the completed transfer subtype rule map.
    return transfer_rule_map

def classify_transactions(xlsx_file,description_column_name,amount_values):

    """Classify each transaction as a transfer, income, expense, or zero amount."""

    # Define the error displayed when transaction amounts cannot be classified.
    invalid_amount_error = "Unable to classify transactions because one or more 'amounts are missing or invalid.'"
    

    # Confirm that the amount data is not empty and contains no missing values.
    if amount_values.empty or amount_values.isna().any():
        raise ValueError(invalid_amount_error)

    # Retrieve the transaction descriptions from the statement.
    normalized_descriptions = xlsx_file[
        description_column_name
    ]

    # Normalize the descriptions for consistent identifier matching.
    normalized_descriptions = (
        normalized_descriptions
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    # Combine the default and user-provided transfer identifiers.
    transfer_identifiers = default_transfer_identifiers + user_transfer_identifiers
    

    # Create a Boolean Series that initially marks every transaction as
    # not being a transfer.
    transfer_mask = pd.Series(False,index=xlsx_file.index)

    # Check the transaction descriptions for each transfer identifier.
    for transfer_identifier in transfer_identifiers:

        # Mark descriptions containing the current transfer identifier.
        current_identifier_mask = (
            normalized_descriptions.str.contains(
                transfer_identifier,
                regex=False
            )
        )

        # Add the current matches to the complete transfer mask.
        transfer_mask = (
            transfer_mask | current_identifier_mask
        )

    # Initially classify every transaction as a zero-amount transaction.
    transaction_types = pd.Series(
        zero_amount_transaction_type,
        index=xlsx_file.index,
        dtype="object"
    )

    # Initially classify every transaction as a zero-amount transaction.
    transaction_types = pd.Series(
        zero_amount_transaction_type,
        index=xlsx_file.index,
        dtype="object"
    )

    # Classify every positive amount as income.
    transaction_types.loc[
        amount_values > 0
    ] = income_transaction_type

    # Classify every negative amount as an expense.
    transaction_types.loc[
        amount_values < 0
    ] = expense_transaction_type

    # Return the transaction type assigned to every statement row.
    return transaction_types

def create_category_rule_map(user_category_identifiers):

    # Define the keys used to separate user and default identifiers.
    user_identifier_key = "user identifiers"
    default_identifier_key = "default identifiers"


    # Define the default identifiers for each income and expense category.
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

    # Map accepted user section names to their canonical transaction types.
    valid_section_names =  {
        "income" : income_transaction_type,
        "expense": expense_transaction_type
    }

    # Define the approved categories for each transaction type.
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

    # Use an empty dictionary when no user identifiers are provided.
    if user_category_identifiers is None:
        user_category_identifiers = {}

    # Confirm that the user category identifiers are provided as a dictionary.
    elif not isinstance(user_category_identifiers,dict):
        raise TypeError("User category identifiers must be provided as a dictionary.")

    # Create a dictionary for the normalized user identifiers.
    normalized_user_identifiers = {}

    # Create an empty user identifier list for every supported category.
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

    # Process every user-provided category section.
    for section_name, category_section in (
        user_category_identifiers.items()):
     # Confirm that the section name is a text value.
        if not isinstance(section_name, str):
            raise TypeError("Category section and category names must be text value.")

        # Normalize the section name for consistent comparison.
        normalized_section_name = (
            section_name
            .strip()
            .lower()
        )

        # Confirm that the section name is supported.
        if normalized_section_name not in valid_section_names:
            raise ValueError(
                "User category identifiers contain an unsupported category."
            )

        # Retrieve the canonical name of the category section.
        canonical_section_name = valid_section_names[
            normalized_section_name
        ]

        # Confirm that the category section is provided as a dictionary.
        if not isinstance(category_section, dict):
            raise TypeError(
                "Each category section must be provided as a dictionary."
            )

        # Process every category and identifier collection in the section.
        for category_name, identifier_collection in (
            category_section.items()
        ):
            # Confirm that the category name is a text value.
            if not isinstance(category_name, str):
                raise TypeError(
                    "Category section and category names must be text value."
                )

            # Normalize the category name for consistent comparison.
            normalized_category_name = (
                category_name
                .strip()
                .lower()
            )

            # Prepare to store the approved version of the category name.
            canonical_category_name = None

            # Compare the category name against the approved categories.
            for approved_category_name in (
                valid_categories_by_section[
                    canonical_section_name
                ]
            ):
                # Normalize the approved category name for comparison.
                normalized_approved_category_name = (
                    approved_category_name.lower()
                )

                # Store the approved category name when a match is found.
                if (
                    normalized_category_name
                    == normalized_approved_category_name
                ):
                    canonical_category_name = (
                        approved_category_name
                    )

                    break

        # Stop processing when the provided category is unsupported.
        if canonical_category_name is None:
            raise ValueError(
                "User category identifiers contain an unsupported category."
            )

        # Confirm that the identifiers are provided as a collection.
        if not isinstance(
            identifier_collection,
            (list, tuple, set)
        ):
            raise TypeError(
                "Category identifiers must be provided as a collection of text values."
            )

        # Retrieve the list that will store the normalized identifiers.
        normalized_identifiers = (
            normalized_user_identifiers[
                canonical_section_name
            ][
                canonical_category_name
            ]
        )

        # Track identifiers that have already been added.
        seen_identifiers = set(
            normalized_identifiers
        )

        # Validate and normalize every user-provided identifier.
        for identifier in identifier_collection:
            # Confirm that the identifier is a text value.
            if not isinstance(identifier, str):
                raise TypeError(
                    "Each category identifier must be a text value."
                )

            # Remove surrounding spaces and convert the identifier to lowercase.
            normalized_identifier = (
                identifier
                .strip()
                .lower()
            )

            # Ignore empty identifiers.
            if normalized_identifier == "":
                continue

            # Ignore identifiers that have already been added.
            if normalized_identifier in seen_identifiers:
                continue

            # Add the normalized identifier to its category.
            normalized_identifiers.append(
                normalized_identifier
            )

            # Mark the identifier as already added.
            seen_identifiers.add(
                normalized_identifier
            )

    # Process every normalized category section.
    for canonical_section_name in normalized_user_identifiers:
        current_normalized_user_section = (
            normalized_user_identifiers[
                canonical_section_name
            ]
        )

        # Sort the user identifiers stored in every category.
        for canonical_category_name in (
            current_normalized_user_section
        ):
            current_normalized_user_section[
                canonical_category_name
            ].sort()

    # Create the final category rule map.
    category_rule_map = {}

    # Process each default income and expense section.
    for (
        canonical_section_name,
        default_category_section
    ) in default_category_identifiers.items():

        # Create the category dictionary for the current section.
        category_rule_map[
            canonical_section_name
        ] = {}

        # Process each category and its default identifiers.
        for (
            canonical_category_name,
            default_identifiers
        ) in default_category_section.items():

            # Retrieve the normalized user identifiers for the category.
            user_identifiers = normalized_user_identifiers[
                canonical_section_name
            ][
                canonical_category_name
            ]

            # Store the user and default identifiers separately.
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

    # Return the completed category rule map.
    return category_rule_map 

def categorize_transactions(xlsx_file,description_column_name,transaction_types,transfer_subtypes,category_rule_map):

   # Define error messages for invalid or misaligned categorization data.
    missing_description_column_error = "The transaction description column could not be found."
    misaligned_transaction_types_error = "Transaction types do not align with the statement transactions."
    misaligned_transfer_subtypes_error = "Transfer subtypes do not align with the statement transactions."
    invalid_category_rule_map_error = "Category rule map must be provided as a dictionary."
    incomplete_category_rule_map_error = "Category rule map must contain both Income and Expense rules."
    invalid_transaction_type_error = "Unable to categorize transaction because its transaction type is invalid."
    invalid_transfer_subtype_error = "Unable to categorize transaction because its transfer subtype is invalid."

    # Define the order in which expense categories are evaluated.
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

    # Define the order in which income categories are evaluated.
    income_categories = [
       employment_income_category,
        refund_reimbursement_category
    ]

    # Define the category rule keys and matching priority values.
    user_identifier_key = "user identifiers"
    default_identifier_key = "default identifiers"
    user_identifier = 2
    default_identifier = 1

    # Define the categories assigned to personal and unclassified transfers.
    incoming_transfers_category = "Incoming Transfers"
    outgoing_transfers_category = "Outgoing Transfers"


    # Confirm that the description column exists in the statement.
    if description_column_name not in xlsx_file.columns:
        raise ValueError( missing_description_column_error)

    # Confirm that the transaction types align with the statement rows.
    if not transaction_types.index.equals(xlsx_file.index):
        raise ValueError(misaligned_transaction_types_error)

    # Confirm that the transfer subtypes align with the statement rows.
    if not transfer_subtypes.index.equals(xlsx_file.index):
        raise ValueError(misaligned_transfer_subtypes_error)

    # Confirm that the category rules are provided as a dictionary.
    if not isinstance(category_rule_map,dict):
        raise TypeError(invalid_category_rule_map_error)

    # Confirm that the rule map contains income and expense rules.
    if (income_transaction_type not in category_rule_map or expense_transaction_type not in category_rule_map):
        raise ValueError(incomplete_category_rule_map_error)

    # Retrieve and normalize the transaction descriptions.
    normalized_descriptions = xlsx_file[description_column_name]
    normalized_descriptions = normalized_descriptions.fillna("").astype(str).str.strip().str.lower()

    # Create an empty Series for the transaction category results.
    transaction_categories = pd.Series(pd.NA,index=xlsx_file.index, dtype = "object")

    # Categorize each transaction in the statement.
    for transaction_index in xlsx_file.index:

        # Retrieve the current transaction's classification data.
        transaction_type = transaction_types.loc[transaction_index]
        transfer_subtype = transfer_subtypes.loc[transaction_index]
        normalized_description = normalized_descriptions.loc[transaction_index]

        # Confirm that the transaction has a supported transaction type.
        if transaction_type not in (income_transaction_type, expense_transaction_type, zero_amount_transaction_type):
            raise ValueError(invalid_transaction_type_error)
        
        # Confirm that the transaction has a supported transfer subtype.
        if transfer_subtype not in (personal_transfer, owned_account_transfer, unclassified_transfer,not_a_transfer):
            raise ValueError(invalid_transfer_subtype_error) 


        # Leave zero-amount transactions uncategorized.
        if transaction_type == zero_amount_transaction_type:
            continue

        # Leave transfers between the user's accounts uncategorized.
        if transfer_subtype == owned_account_transfer:
            continue

        # Categorize personal and unclassified transfers by their direction.
        if transfer_subtype in (personal_transfer, unclassified_transfer):

             # Categorize incoming transfers.
             if transaction_type == income_transaction_type:
                transaction_categories.loc[
                    transaction_index
                    ] = incoming_transfers_category

             # Categorize outgoing transfers.
             elif transaction_type == expense_transaction_type:
                    transaction_categories.loc[
                    transaction_index
                ] = outgoing_transfers_category 

             continue 

        # Select the income rules, category priority, and fallback category.
        if transaction_type == income_transaction_type:

                applicable_category_rules = category_rule_map[income_transaction_type]

                category_priority = income_categories
                fallback_category = other_income_category 

        # Select the expense rules, category priority, and fallback category.
        else: 
            applicable_category_rules = category_rule_map[expense_transaction_type]

            category_priority = expense_categories
            fallback_category = other_expense_category

        # Use the fallback category when the transaction description is empty.
        if normalized_description == "":
                transaction_categories.loc[
                transaction_index
            ] = fallback_category

                continue 

        # Prepare to track the strongest category match.
        selected_category = pd.NA
        best_source_priority = 0
        best_identifier_length = 0

        # Search the categories in their assigned priority order.
        for category_name in category_priority:

            # Retrieve the identifier rules for the current category.
            category_rules = applicable_category_rules[
                category_name
            ]

            # Search user identifiers before default identifiers.
            for identifier_source in (user_identifier_key, default_identifier_key):

                # Assign the matching priority for the identifier source.
                if identifier_source == user_identifier_key:
                    source_priority = user_identifier

                else:
                    source_priority = default_identifier

                # Retrieve the identifiers from the current source.
                identifiers = category_rules[identifier_source]

                # Compare each identifier with the transaction description.
                for identifier in identifiers:

                    if  identifier in normalized_description:

                        # Measure the matching identifier's specificity.
                        identifier_length = len(identifier)

                        # Select matches from the higher-priority source.
                        if source_priority > best_source_priority:
                            selected_category = category_name
                            best_source_priority = source_priority
                            best_identifier_length = identifier_length

                        # Prefer the longer identifier when priorities are equal.
                        elif (source_priority == best_source_priority and identifier_length > best_identifier_length):
                            selected_category = category_name
                            best_identifier_length = identifier_length

        # Assign the category selected by the identifier rules.
        if pd.notna(selected_category):

            transaction_categories.loc[
                transaction_index
            ] = selected_category

        # Use the fallback category when no identifier matches.
        else:
            transaction_categories.loc[
            transaction_index
        ] = fallback_category

    # Return the category assigned to every transaction.
    return transaction_categories          

def calculate_category_totals(amount_values,transaction_types,transaction_categories):
    
    # Define the supported income categories and their display order.
    income_categories = [
        employment_income_category,
        refund_reimbursement_category,
        incoming_transfers_category,
        other_income_category
    ]

    # Define the supported expense categories and their display order.
    expense_categories = [
        housing_category,
        utilities_category,
        healthcare_category,
        transportation_category,
        groceries_category,
        dining_category,
        entertainment_category,
        shopping_category,
        outgoing_transfers_category,
        other_expense_category
        ]

    # Confirm that the transaction amounts are provided as a pandas Series.
    if not isinstance(amount_values,pd.Series):
        raise TypeError("Amount values must be provided as a pandas Series.")

    # Confirm that the transaction types are provided as a pandas Series.
    if not isinstance(transaction_types,pd.Series):
        raise TypeError("Transaction types must be provided as a pandas Series.")

    # Confirm that the transaction categories are provided as a pandas Series.
    if not isinstance(transaction_categories,pd.Series):
        raise TypeError("Transaction categories must be provided as a pandas Series.")

    # Confirm that the transaction types align with the transaction amounts.
    if not transaction_types.index.equals(amount_values.index):
        raise ValueError("Transaction types do not align with the transaction amounts.")

    # Confirm that the transaction categories align with the transaction amounts.
    if not transaction_categories.index.equals(amount_values.index):
        raise ValueError("Transaction categories do not align with the transaction amounts.")

    # Stop the calculation when any transaction amount is missing.
    if amount_values.isna().any():
        raise ValueError("Unable to calculate category totals because one or more amounts are missing or invalid.")

    # Confirm that the transaction amounts contain numeric values.
    if not pd.api.types.is_numeric_dtype(amount_values):
        raise ValueError("Unable to calculate category totals because one or more amounts are missing or invalid.") 

    # Return empty category totals when there are no transaction amounts.
    if amount_values.empty:
        income_category_totals = pd.Series(dtype = "float")
        expense_category_totals = pd.Series(dtype = "float")
        return income_category_totals,expense_category_totals

    # Validate the type, amount, and category of every transaction.
    for transaction_index in amount_values.index:

        # Retrieve the current transaction amount and transaction type.
        transaction_amount = amount_values.loc[transaction_index]
        transaction_type = transaction_types.loc[transaction_index]

        # Retrieve the current transaction category.
        transaction_category = transaction_categories.loc[transaction_index]

        # Confirm that the transaction has a supported transaction type.
        if transaction_type not in (income_transaction_type,expense_transaction_type,zero_amount_transaction_type):
            raise ValueError("Unable to calculate category totals because a transaction type is invalid.")

        # Validate income transactions.
        if transaction_type == income_transaction_type:

            # Confirm that an income transaction has a positive amount.
            if transaction_amount <= 0:
                raise ValueError("A transaction amount does not match its transaction type.")

            # Skip income transactions that do not have a category.
            if pd.isna(transaction_category):
                continue

            # Confirm that the transaction uses a supported income category.
            if transaction_category not in income_categories:
                raise ValueError("A transaction category does not match its transaction type.")

        # Validate expense transactions.
        elif transaction_type == expense_transaction_type:

            # Confirm that an expense transaction has a negative amount.
            if transaction_amount >= 0:
                raise ValueError("A transaction amount does not match its transaction type.")

            # Skip expense transactions that do not have a category.
            if pd.isna(transaction_category):
                continue

            # Confirm that the transaction uses a supported expense category.
            if transaction_category not in expense_categories:
                raise ValueError("A transaction category does not match its transaction type.")

        # Validate zero-amount transactions.
        else:

            # Confirm that a zero-amount transaction has an amount of zero.
            if transaction_amount != 0:
                raise ValueError("A transaction amount does not match its transaction type.")

            # Confirm that a zero-amount transaction does not have a category.
            if  pd.notna(transaction_category):
                raise ValueError("A transaction category does not match its transaction type.")

    # Combine the transaction data into a DataFrame for category calculations.
    category_data = pd.DataFrame({"amount":amount_values,"transaction_type": transaction_types,"transaction_category": transaction_categories})

    # Remove transactions that do not have an assigned category.
    categorized_data = category_data.dropna(subset=["transaction_category"])

    # Select transactions categorized as income.
    income_data = categorized_data[categorized_data["transaction_type"] == income_transaction_type]

    # Calculate the total amount for each income category.
    income_category_totals = income_data.groupby("transaction_category")["amount"].sum()

    # Arrange the income totals in the defined category order.
    income_category_totals = income_category_totals.reindex(income_categories, fill_value=0)

    # Remove income categories that have a total of zero.
    income_category_totals = income_category_totals[income_category_totals != 0]

    # Convert the income category totals to floating-point values.
    income_category_totals = income_category_totals.astype(float)

    # Select transactions categorized as expenses.
    expense_data = categorized_data[categorized_data["transaction_type"] == expense_transaction_type]

    # Calculate the total amount for each expense category.
    expense_category_totals = expense_data.groupby("transaction_category")["amount"].sum()

    # Convert the negative expense totals into positive values.
    expense_category_totals = expense_category_totals.abs()

    # Arrange the expense totals in the defined category order.
    expense_category_totals = expense_category_totals.reindex(expense_categories, fill_value=0)

    # Remove expense categories that have a total of zero.
    expense_category_totals = expense_category_totals[expense_category_totals != 0]

    # Convert the expense category totals to floating-point values.
    expense_category_totals = expense_category_totals.astype(float)

    # Return the calculated income and expense category totals.
    return income_category_totals, expense_category_totals

# ============================================================
# FINANCIAL CALCULATION FUNCTIONS
# ============================================================
def count_transactions(xlsx_file):

    transaction_count = len(xlsx_file)

    return transaction_count

def calculate_financial_summary(xlsx_file,description_column_name):

     # Count the total number of transactions in the statement.
    transaction_count = count_transactions(xlsx_file)

    # Identify the column containing the transaction amounts.
    amount_column_name = identify_amount_column(xlsx_file)

    # Retrieve the transaction amounts from the statement.
    amount_values = xlsx_file[amount_column_name]

    # Convert the transaction amounts into text for cleaning.
    amount_values = amount_values.astype(str)

    # Remove dollar signs from the transaction amounts.
    amount_values = amount_values.str.replace("$","",regex=False)

    # Remove commas from the transaction amounts.
    amount_values = amount_values.str.replace(",","",regex=False)

    # Convert the cleaned transaction amounts into numeric values.
    amount_values = pd.to_numeric(amount_values,errors="coerce")

    # Classify each transaction using its description and amount.
    transaction_types = classify_transactions(xlsx_file,description_column_name,amount_values)

    # Select the amounts classified as income.
    income_amounts = amount_values[
        transaction_types == income_transaction_type
    ]

    # Select the amounts classified as expenses.
    expense_amounts = amount_values[
        transaction_types == expense_transaction_type
    ]

    # Calculate the total income.
    total_income = income_amounts.sum()

    # Calculate the total expenses.
    total_expenses = expense_amounts.sum()

    # Calculate the balance remaining after expenses.
    net_balance = (
        total_income + total_expenses
    )

    # Return the complete financial summary and transaction data.
    return (
        transaction_count,
        total_income,
        total_expenses,
        net_balance,
        amount_values,
        transaction_types
    )

def calculate_monthly_summary(xlsx_file,date_column_name, amount_values,transaction_types,transfer_subtypes):

    # Confirm that the statement data is a DataFrame.
    if not isinstance(xlsx_file, pd.DataFrame):
        raise TypeError(
            "Statement data must be provided as a pandas DataFrame."
        )

    # Confirm that the requested date column exists.
    if date_column_name not in xlsx_file.columns:
        raise ValueError(
            "The transaction date column could not be found."
        )

    # Confirm that the amount values are a pandas Series.
    if not isinstance(amount_values, pd.Series):
        raise TypeError(
            "Amount values must be provided as a pandas Series."
        )

    # Confirm that the transaction types are a pandas Series.
    if not isinstance(transaction_types, pd.Series):
        raise TypeError(
            "Transaction types must be provided as a pandas Series."
        )

    # Confirm that the transfer subtypes are a pandas Series.
    if not isinstance(transfer_subtypes, pd.Series):
        raise TypeError(
            "Transfer subtypes must be provided as a pandas Series."
        )

    # Confirm that all monthly data uses the statement index.
    if (
        not amount_values.index.equals(xlsx_file.index)
        or not transaction_types.index.equals(xlsx_file.index)
        or not transfer_subtypes.index.equals(xlsx_file.index)
    ):
        raise ValueError(
            "Monthly transaction data does not align with " 
            "the statement transactions."
        )

    approved_transaction_types = {
    income_transaction_type,
    expense_transaction_type,
    zero_amount_transaction_type
}

    # Confirm that all amount values are present and numeric.
    if (
        amount_values.isna().any()
        or not pd.api.types.is_numeric_dtype(amount_values)
    ):
        raise ValueError(
            "Monthly amount values must contain valid numeric values."
        )

    # Confirm that every transaction type is approved.
    if (
        transaction_types.isna().any()
        or not transaction_types.isin(
            approved_transaction_types
        ).all()
    ):
        raise ValueError(
            "Monthly data contains an unsupported transaction type."
        )

    # Confirm that Income transactions contain positive amounts.
    if (
        amount_values[
            transaction_types == income_transaction_type
        ] <= 0
    ).any():
        raise ValueError(
            "A transaction amount does not match its transaction type."
        )

    # Confirm that Expense transactions contain negative amounts.
    if (
        amount_values[
            transaction_types == expense_transaction_type
        ] >= 0
    ).any():
        raise ValueError(
            "A transaction amount does not match its transaction type."
        )

    # Confirm that Zero Amount transactions contain zero.
    if (
        amount_values[
            transaction_types == zero_amount_transaction_type
        ] != 0
    ).any():
        raise ValueError(
            "A transaction amount does not match its transaction type."
        )   
    # Combine the dates, amounts, and transaction types into one DataFrame.
    monthly_data = pd.DataFrame({
        "date": xlsx_file[date_column_name],
        "amount": amount_values,
        "transaction_type": transaction_types,
        "transfer_subtype": transfer_subtypes
    })

    # Convert the statement dates into pandas datetime values.
    monthly_data["date"] = pd.to_datetime(
        monthly_data["date"],
        errors="coerce"
    )

    # Confirm that at least one usable transaction date exists.
    if monthly_data["date"].isna().all():
        raise ValueError(
            "No valid transaction dates were found "
            "for the monthly summary."
        )

   # Remove transactions with missing monthly calculation data.
    monthly_data = monthly_data.dropna(
        subset=[
            "date",
            "amount",
            "transaction_type",
            "transfer_subtype"
        ]
    )

    # Create the year-month value used to group transactions.
    monthly_data["month"] = (
        monthly_data["date"].dt.to_period("M")
    )

    # Select the transactions classified as income.
    monthly_income = monthly_data[
        monthly_data["transaction_type"]
        == income_transaction_type
    ]

    # Select the transactions classified as expenses.
    monthly_expenses = monthly_data[
        monthly_data["transaction_type"]
        == expense_transaction_type
    ]

    # Calculate the total income for each month.
    monthly_income_totals = (
        monthly_income.groupby("month")["amount"].sum()
    )

    # Calculate the total expenses for each month.
    monthly_expense_totals = (
        monthly_expenses.groupby("month")["amount"].sum()
    )

    # Count the income transactions in each month.
    monthly_income_transaction_counts = (
        monthly_income.groupby("month").size()
    )

    # Count the expense transactions in each month.
    monthly_expense_transaction_counts = (
        monthly_expenses.groupby("month").size()
    )

    # Count all transactions in each month and sort them chronologically.
    monthly_transactions = (
        monthly_data.groupby("month").size().sort_index()
    )

    # Retrieve the months that contain transaction data.
    months = monthly_transactions.index

   
    # Align the monthly income totals with the complete month list.
    monthly_income_totals = (
        monthly_income_totals.reindex(
            months,
            fill_value=0
        )
    )

    # Align the monthly expense totals with the complete month list.
    monthly_expense_totals = (
        monthly_expense_totals.reindex(
            months,
            fill_value=0
        )
    )

    # Align the monthly income transaction counts with the complete month list.
    monthly_income_transaction_counts = (
        monthly_income_transaction_counts.reindex(
            months,
            fill_value=0
        )
    )

    # Align the monthly expense transaction counts with the complete month list.
    monthly_expense_transaction_counts = (
        monthly_expense_transaction_counts.reindex(
            months,
            fill_value=0
        )
    )

    # Define the transfer subtypes included in monthly transfer counts.
    recognized_transfer_subtypes = {
        personal_transfer,
        owned_account_transfer,
        unclassified_transfer
    }

    # Select Income transactions identified as transfers.
    incoming_transfers = monthly_income[
        monthly_income["transfer_subtype"].isin(
            recognized_transfer_subtypes
        )
    ]

    # Select Expense transactions identified as transfers.
    outgoing_transfers = monthly_expenses[
        monthly_expenses["transfer_subtype"].isin(
            recognized_transfer_subtypes
        )
    ]

    # Count the incoming transfer transactions in each month.
    monthly_incoming_transfer_counts = (
        incoming_transfers.groupby("month").size()
    )

    # Count the outgoing transfer transactions in each month.
    monthly_outgoing_transfer_counts = (
        outgoing_transfers.groupby("month").size()
    )

    # Align the incoming transfer counts with the complete month list.
    monthly_incoming_transfer_counts = (
        monthly_incoming_transfer_counts.reindex(
            months,
            fill_value=0
        )
    )

    # Align the outgoing transfer counts with the complete month list.
    monthly_outgoing_transfer_counts = (
        monthly_outgoing_transfer_counts.reindex(
            months,
            fill_value=0
        )
    )

    # Confirm that incoming transfers do not exceed Income transactions.
    if (
        monthly_incoming_transfer_counts
        > monthly_income_transaction_counts
    ).any():
        raise ValueError(
            "A monthly incoming transfer count exceeds "
            "the total Income transaction count."
        )

    # Confirm that outgoing transfers do not exceed Expense transactions.
    if (
        monthly_outgoing_transfer_counts
        > monthly_expense_transaction_counts
    ).any():
        raise ValueError(
            "A monthly outgoing transfer count exceeds "
            "the total Expense transaction count."
        )

   # Convert the internal year-month values into display month names.
    months = months.strftime("%B").tolist()

    # Convert the monthly income totals into a list.
    income_totals = (
        monthly_income_totals.tolist()
    )

    # Convert the expense totals into positive values and store them in a list.
    expense_totals = (
        monthly_expense_totals.abs().tolist()
    )

    # Convert the monthly income transaction counts into a list.
    income_transaction_counts = (
        monthly_income_transaction_counts.tolist()
    )

    # Convert the monthly expense transaction counts into a list.
    expense_transaction_counts = (
        monthly_expense_transaction_counts.tolist()
    )

    # Convert the monthly incoming transfer counts into a list.
    incoming_transfer_counts = (
        monthly_incoming_transfer_counts.tolist()
    )

    # Convert the monthly outgoing transfer counts into a list.
    outgoing_transfer_counts = (
        monthly_outgoing_transfer_counts.tolist()
    )

    # Return the monthly totals and transaction counts.
    return (
        months,
        income_totals,
        expense_totals,
        income_transaction_counts,
        expense_transaction_counts,
        incoming_transfer_counts,
        outgoing_transfer_counts
    )

# ============================================================
# AI FINANCIAL INSIGHT FUNCTIONS
# ============================================================
def prepare_financial_insight_data(
    financial_summary,
    monthly_summary,
    financial_health_summary,
    reporting_period
):

   required_financial_summary_length = 6
   required_financial_health_summary_length = 2 
   required_monthly_summary_length = 7
   required_reporting_period_length = 2
   date_display_format = "%B %d, %Y"
   unavailable_savings_rate_text = "N/A"

   financial_health_status_map = {
    "very healthy": "Very Healthy",
    "healthy": "Healthy",
    "needs attention": "Needs Attention",
    "caution": "Caution",
    "weak": "Weak",
    "at risk": "At Risk",
    "very weak": "Very Weak",
    "unable to determine": "Unable to Determine"
    } 


   if not isinstance(financial_summary, tuple):
       raise TypeError("Financial summary must be provided as a tuple.")

   if  len(financial_summary) != required_financial_summary_length:
       raise ValueError("Financial summary must contain six values.")
       
   if not isinstance(monthly_summary, tuple):
       raise TypeError("Monthly summary must be provided as a tuple.")

   if  len(monthly_summary) != required_monthly_summary_length:
       raise ValueError("Monthly summary must have a legth of seven.")

   if not isinstance(financial_health_summary, tuple):
       raise TypeError("Financial health summary must be provided as a tuple.")

   if len(financial_health_summary) != required_financial_health_summary_length:
       raise ValueError("Financial health summary must have two values.")

   if not isinstance(reporting_period, tuple):
       raise TypeError("Reporting period must be provided as a tuple.")
   
   if len(reporting_period) !=  required_reporting_period_length:
       raise ValueError("Reporting period must contain two values.")

   (
        transaction_count,
        total_income,
        total_expenses,
        net_balance,
        amount_values,
        transaction_types
    ) = financial_summary


    # Retrieve the monthly summary values.
   (
    months,
    income_totals,
    expense_totals,
    income_transaction_counts,
    expense_transaction_counts,
    income_transfer_counts,
    expense_transfer_counts
    ) = monthly_summary

    # Retrieve the Financial Health values.
   (
    financial_health,
    savings_rate
    ) = financial_health_summary

    # Retrieve the reporting-period dates.
   (
    start_date,
    end_date
    ) = reporting_period
    

   if start_date == end_date:
       raise ValueError("Start and end dates are identical.")

   if start_date > end_date:
       start_date, end_date = end_date, start_date

    # Format the reporting-period dates for display.
   formatted_start_date = start_date.strftime(
        date_display_format
    )

   formatted_end_date = end_date.strftime(
        date_display_format
    )

    # Normalize the Financial Health status.
   if not isinstance(financial_health, str):
        raise TypeError("Financial Health status must be text.")

   financial_health_key = (financial_health.strip().casefold())

   if financial_health_key not in financial_health_status_map:
        raise ValueError("Financial Health contains an unsupported status.")

   normalized_financial_health = (financial_health_status_map[financial_health_key])

   if savings_rate is None:
       formatted_savings_rate = unavailable_savings_rate_text

   else:
       formatted_savings_rate = f"{savings_rate:,.2f}%"

   formatted_total_income = f"${total_income:,.2f}"
   formatted_total_expenses = (f"${abs(total_expenses):,.2f}")

   if net_balance < 0:
       formatted_net_balance = f"-${abs(net_balance):,.2f}"

   else:
       formatted_net_balance = f"${net_balance:,.2f}"

   normalized_month_names = set()
   monthly_income_expense_records = []
   monthly_transaction_records = []

   combined_monthly_income = 0
   combined_monthly_expenses = 0
   total_income_transaction_count = 0
   total_expense_transaction_count = 0
   total_income_transfer_count = 0
   total_expense_transfer_count = 0
   total_non_transfer_income_count = 0
   total_non_transfer_expense_count = 0

   for (
    month,
    income_total,
    expense_total,
    income_transaction_count,
    expense_transaction_count,
    income_transfer_count,
    expense_transfer_count
    ) in zip(
        months,
        income_totals,
        expense_totals,
        income_transaction_counts,
        expense_transaction_counts,
        income_transfer_counts,
        expense_transfer_counts
    ):

        if not isinstance(month,str):
            raise TypeError("Month names must be provided as text.")

        normalized_month = month.strip()

        if not normalized_month:
            raise ValueError("Month names cannot be empty.")


        if normalized_month in normalized_month_names:
            raise ValueError("Month already exists in the months list.")

        normalized_month_names.add(normalized_month)

        if income_transfer_count > income_transaction_count:
            raise ValueError("Income transfers exceed the income transaction count.")

        if expense_transfer_count > expense_transaction_count:
            raise ValueError("Expense transfers exceed the expense transfers.")

        non_transfer_income_count = income_transaction_count - income_transfer_count
        non_transfer_expense_count = expense_transaction_count - expense_transfer_count

        formatted_income_total = (f"${income_total:,.2f}")

        formatted_expense_total = (f"${abs(expense_total):,.2f}")

        # Store the current month's income and expense amounts.
        monthly_income_expense_record = {
            "Month": normalized_month,
            "Income": formatted_income_total,
            "Expenses": formatted_expense_total
        }

        # Store the current month's transaction and transfer counts.
        monthly_transaction_record = {
            "Month": normalized_month,
            "Total Income Transactions": income_transaction_count,
            "Income Transfers": income_transfer_count,
            "Non-Transfer Income Transactions": non_transfer_income_count,
            "Total Expense Transactions": expense_transaction_count,
            "Expense Transfers": expense_transfer_count,
            "Non-Transfer Expense Transactions": non_transfer_expense_count
        }

        monthly_income_expense_records.append(monthly_income_expense_record)

        monthly_transaction_records.append(monthly_transaction_record)

        combined_monthly_income = combined_monthly_income + income_total
        combined_monthly_expenses = combined_monthly_expenses + (abs(expense_total))

        total_income_transaction_count =  total_income_transaction_count + income_transaction_count
        total_expense_transaction_count = total_expense_transaction_count + expense_transaction_count

        total_income_transfer_count = total_income_transfer_count + income_transfer_count
        total_expense_transfer_count = total_expense_transfer_count + expense_transfer_count

        total_non_transfer_income_count = total_non_transfer_income_count + non_transfer_income_count
        total_non_transfer_expense_count = total_non_transfer_expense_count +non_transfer_expense_count

    
   unrepresented_income_amount = total_income - combined_monthly_income
   unrepresented_expense_amount = abs(total_expenses) - combined_monthly_expenses
   unrepresented_transaction_count = transaction_count - total_income_transaction_count - total_expense_transaction_count

   if round(unrepresented_income_amount, 2) < 0:
        raise ValueError("Monthly income exceed total income.")

   if round(unrepresented_expense_amount, 2) < 0:     
       raise ValueError("Monthly expenses exceed total expenses.")

   if unrepresented_transaction_count < 0: 
       raise ValueError("Monthly transaction count exceed the table transaction count.")

   reporting_period_section = {
       "Start Date": formatted_start_date,
       "End Date": formatted_end_date
   }

   financial_summary_table_section = {
       "Transaction Count": transaction_count,
       "Total Income": formatted_total_income,
       "Total Expenses": formatted_total_expenses,
       "Net Balance": formatted_net_balance
   }       

   financial_health_section = {
       "Status": normalized_financial_health,
       "Savings Rate": formatted_savings_rate
   }

   # Store the completed monthly income and expense records.
   monthly_income_expense_section = {
        "Monthly Records": monthly_income_expense_records
    }

   if round(unrepresented_income_amount, 2) > 0:
       monthly_income_expense_section["Income Not Represented in Monthly Totals"] = f"${unrepresented_income_amount:,.2f}"

   if round(unrepresented_expense_amount, 2) > 0:
       monthly_income_expense_section["Expenses Not Represented in Monthly Totals"] = f"${unrepresented_expense_amount:,.2f}"

   income_expense_transaction_section = {
        "Total Income Transactions": total_income_transaction_count,
        "Total Expense Transactions": total_expense_transaction_count,
        "Income Transfers": total_income_transfer_count,
        "Non-Transfer Income Transactions": total_non_transfer_income_count,
        "Expense Transfers": total_expense_transfer_count,
        "Non-Transfer Expense Transactions": total_non_transfer_expense_count,
        "Monthly Records":monthly_transaction_records
    }

   if unrepresented_transaction_count > 0:
       income_expense_transaction_section[
           "Transactions Not Represented in Monthly Income/Expense Counts"
           ] = unrepresented_transaction_count

   financial_insight_data  = {
       "Reporting Period": reporting_period_section,
       "Financial Summary Table": financial_summary_table_section,
       "Financial Health": financial_health_section,
       "Monthly Income vs. Expenses": monthly_income_expense_section,
       "Income vs. Expense Transactions": income_expense_transaction_section
   } 

   return financial_insight_data
def generate_financial_insights(financial_insight_data):

    class FinancialInsightResponse(BaseModel):

    financial_summary_table: str
    financial_health: str
    monthly_income_expenses: str
    income_expense_transactions: str


    # Define the project-specific error raised when insight generation fails.
    class FinancialInsightGenerationError(Exception):
        pass


    # Define the OpenAI model used to generate financial insights.
    financial_insight_model = "gpt-5.6-terra"

    # Define the maximum number of tokens allowed in the generated response.
    maximum_financial_insight_output_tokens = 1500

    openai_api_key = "OPENAI_API_KEY"
    json_indentation = 4
    required_disclaimer = "This summary is informational and not financial advice."

    required_financial_insight_sections = {
        "Reporting Period",
        "Financial Summary Table",
        "Financial Health",
        "Monthly Income vs. Expenses",
        "Income vs. Expense Transactions"
    }

    if not isinstance(financial_insight_data, dict):
        raise TypeError("Daata must be a dictionary.")

    if financial_insight_data is None:
        raise ValueError("Financial insight data is empty.")

    received_financial_insight_sections = set(financial_insight_data.keys())

    if  received_financial_insight_sections != required_financial_insight_sections:
        raise ValueError("Financial insight data must contain exactly the five required sections.")

    #  GET openai_api_key from openai_api_key_environment_variable

    if openai_api_key is None:
        raise EnvironmentError("Open API key is missing.")

    if openai_api_key.empty():
        raise EnvironmentError("Open API key is empty.")

    
def validate_financial_insights(financial_insights):
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

    # Confirm that the total income is not negative.
    if total_income < 0:
        raise ValueError(invalid_total_income_error)

    # Convert total expenses into a positive value for the calculation.
    normalized_expenses = abs(total_expenses)

    # Handle financial health calculations when there is no income.
    if total_income == 0:

        # Use no savings rate because it cannot be calculated without income.
        savings_rate = None

        # Use an undetermined status when there is no income or spending.
        if normalized_expenses == 0:
            financial_health = unable_to_determine_status

        # Use the lowest measurable status when spending exists without income.
        else:
            financial_health = very_weak_status

        # Return the result without performing the savings-rate calculation.
        return financial_health, savings_rate

    # Calculate the balance remaining after expenses.
    calculated_net_balance = total_income - normalized_expenses

    # Calculate the percentage of income remaining after expenses.
    savings_rate = (
        calculated_net_balance / total_income
    ) * 100

    # Assign the Very Healthy status.
    if savings_rate >= very_healthy_threshold:
        financial_health = very_healthy_status

    # Assign the Healthy status.
    elif savings_rate >= healthy_threshold:
        financial_health = healthy_status

    # Assign the Needs Attention status.
    elif savings_rate >= needs_attention_threshold:
        financial_health = needs_attention_status

    # Assign the Caution status.
    elif savings_rate >= caution_threshold:
        financial_health = caution_status

    # Assign the Weak status.
    elif savings_rate >= weak_threshold:
        financial_health = weak_status

    # Assign the Very Weak status.
    elif savings_rate >= very_weak_threshold:
        financial_health = very_weak_status

    # Assign the At Risk status when no threshold is reached.
    else:
        financial_health =at_risk_status 

    # Return the financial health status and calculated savings rate.
    return financial_health, savings_rate

def get_financial_health_colors(financial_health):

    # Map each financial health status to its foreground and background colors.
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
    # Define the colors used when the financial health status is not recognized.
    default_colors = ("#666666", "#F2F2F2")

    # Retrieve the colors for the financial health status.
    selected_colors = health_color_map.get(financial_health,default_colors)

    # Separate the selected foreground and background colors.
    (
        status_forground_color,
        status_background_color
    ) = selected_colors

    # Return the foreground and background colors.
    return status_forground_color, status_background_color

def create_financial_health_summary(financial_health_axis,financial_health,savings_rate):
    
   # Define the financial health card's position and dimensions.
    card_x_position = 0.01
    card_y_position = 0.45
    card_width = .98
    card_height = .8

    # Define the positions of the text displayed inside the card.
    common_vertical_position = .80
    title_horizontal_position = .16
    status_label_horizontal_position = .41
    savings_label_horizontal_position = .74
    savings_result_horizontal_position = .75

    # Define the font sizes used for the card text.
    title_font_size = 13
    label_font_size = 11
    result_font_size = 11

    # Define the card border width and corner rounding.
    card_border_width = 1.5
    corner_rounding_size = .03

    # Hide the axis lines, labels, and ticks.
    financial_health_axis.axis("off")

    # Retrieve the foreground and background colors for the health status.
    (
    status_foreground_color,
    status_background_color
    ) = get_financial_health_colors(financial_health)

    # Display N/A when a savings rate could not be calculated.
    if savings_rate == None:
        formatted_saving_rate = "N/A"

    # Format the calculated savings rate as a percentage.
    else:
        formatted_saving_rate = f"{savings_rate:.2f}%"

    # Prepare the financial health status and savings-rate text.
    status_text = financial_health
    savings_rate_text = formatted_saving_rate

    # Create the rounded financial health summary card.
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

    # Add the financial health card to the axis.
    financial_health_axis.add_patch(financial_health_card)

    # Display the financial health title.
    financial_health_axis.text(
        title_horizontal_position,
        common_vertical_position,
        "Financial Health",
        transform=financial_health_axis.transAxes,
        ha="center",
        va="center",
        fontsize=title_font_size,
        fontweight="bold",
        color=status_foreground_color,
        zorder=1
    )

    # Display the status label.
    financial_health_axis.text(
        status_label_horizontal_position,
        common_vertical_position,
        "Status:",
        transform=financial_health_axis.transAxes,
        ha="right",
        va="center",
        fontsize=label_font_size,
        fontweight="normal",
        color="black",
        zorder=1
    )

    # Display the calculated financial health status.
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

    # Display the savings-rate label.
    financial_health_axis.text(
        savings_label_horizontal_position,
        common_vertical_position,
        "Savings Rate:",
        transform=financial_health_axis.transAxes,
        ha="right",
        va="center",
        fontsize=label_font_size,
        fontweight="normal",
        color="black",
        zorder=1
    )

    # Display the formatted savings-rate result.
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

    # Finish the function without returning a value.
    return None
# ============================================================
# TABLE STYLING FUNCTIONS
# ============================================================
def style_financial_table(financial_table):

      # Retrieve the table's cells.
   fin_tab = financial_table.get_celld()

   # Apply formatting to every cell in the financial table.
   for (row, column), cell in fin_tab.items():

        # Style cells in the table's header row.
        if row == 0:
            header_cell = cell
            header_cell.set_facecolor("darkblue")

            # Format the header text.
            header_cell.set_text_props(
                color="white",
                weight="bold",
                fontsize=12,
                ha="center",
                va="center"
            )

            # Format the header cell borders.
            header_cell.set_edgecolor("white")
            header_cell.set_linewidth(1.0)

        # Style cells containing financial data.
        else:
            data_cell = cell

            # Apply alternating background colors to even-numbered rows.
            if row % 2 == 0:
                data_cell.set_facecolor("whitesmoke")

            # Apply a white background to odd-numbered rows.
            else:
                data_cell.set_facecolor("white")

            # Format the data cell text.
            data_cell.set_text_props(
                fontsize=10,
                ha="center",
                va="center"
            )

            # Format the data cell borders.
            data_cell.set_edgecolor("lightgray")
            data_cell.set_linewidth(0.8)

   # Increase the height of the table cells.
   financial_table.scale(1.0, 2.0)

   # Finish the function without returning a value.
   return None
# ============================================================
# INCOME AND EXPENSE CHART FUNCTIONS
# ============================================================
def create_monthly_income_expenses_chart(income_axis,months,income_totals,expense_totals):

        # Set the width of each bar.
    bar_width = 0.15

    # Set the amount of space between the income and expense bars.
    bar_gap = 0.07  
    
    # Calculate the central x-axis position for each month.
    x_positions = np.arange(len(months))

    # Position the income and expense bars on opposite sides of each month.
    income_positions = x_positions - ((bar_width + bar_gap) / 2)
    expense_positions = x_positions + ((bar_width + bar_gap) / 2)

    # Create the monthly income bars.
    income_bars = income_axis.bar(
        income_positions,
        income_totals,
        width=bar_width,
        label="Income",
        color="limegreen",
        alpha = 1.0,
        zorder = 2   
        )

    # Create the monthly expense bars.
    expense_bars = income_axis.bar(
        expense_positions,
        expense_totals,
        width=bar_width,
        label="Expenses",
        color="red",
        alpha = 1.0,
        zorder = 2
    )

    # Position the x-axis tick marks and label them with the months.
    income_axis.set_xticks(x_positions)
    income_axis.set_xticklabels(months)

    # Add the x-axis label, y-axis label, and chart title.
    income_axis.set_xlabel("Month")
    income_axis.set_ylabel("Amount ($)")
    income_axis.set_title("MONTHLY INCOME vs EXPENSES",fontsize=15, fontweight="bold", color="black")

    # Hide the top and right chart borders.
    income_axis.spines["top"].set_visible(False)
    income_axis.spines["right"].set_visible(False)

    # Add horizontal grid lines to make the values easier to compare.
    income_axis.yaxis.grid(
        True,
        linestyle="--",
        alpha = 1.0,
        color = "lightgrey",
        zorder = 2
    )

    # Add the income and expense legend below the chart.
    income_axis.legend(loc = "lower center",bbox_to_anchor=(0.1, -0.35),
    ncol=1,fontsize=11,frameon=False, columnspacing = 5)
    
    # Return the income and expense bar containers.
    return income_bars, expense_bars

def style_monthly_income_expenses_chart(income_axis, income_bars, expense_bars):

    # Retrieve the current lower and upper limits of the y-axis.
    current_ylim, current_ymax = income_axis.get_ylim()

    # Define the space above each label and the additional y-axis space.
    label_offset_percentage = 0.02
    y_axis_expansion_percentage = 0.08

    # Calculate and apply the amount needed to expand the y-axis.
    expansion_amount = current_ymax * y_axis_expansion_percentage
    new_ymax = current_ymax + expansion_amount

    # Calculate the vertical space between each bar and its value label.
    label_offset = current_ymax * label_offset_percentage

    # Add a formatted value label above every income bar.
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
        
    # Add a formatted value label above every expense bar.
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
    
    # Expand the y-axis to provide room for the value labels.
    income_axis.set_ylim(current_ylim, new_ymax)

    # Create the rounded card surrounding the income and expense chart.
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

    # Add the rounded card to the chart.
    income_axis.add_patch(card)

def create_expense_pie_chart(
    pie_axis,
    descriptions,
    amount_values,
    transaction_types,
):
    """
    Create a pie chart showing expenses grouped by spending category.

    Parameters
    ----------
    pie_axis : matplotlib.axes.Axes
        Axis where the expense pie chart will be created.

    descriptions : list
        Transaction descriptions aligned with amount_values
        and transaction_types.

    amount_values : list
        Numeric transaction amounts.

    transaction_types : list
        Transaction classifications such as "Income" or "Expense".

    Returns
    -------
    tuple
        (
            pie_wedges,
            category_labels,
            category_totals,
        )
    """

    # Verify that all transaction collections contain the same
    # number of records.
    if not (
        len(descriptions)
        == len(amount_values)
        == len(transaction_types)
    ):
        raise ValueError(
            "Descriptions, amounts, and transaction types must have matching lengths."
        )

    # Define the keywords used to classify expense transactions.
    expense_category_rule_map = {
        "Groceries": [
            "walmart",
            "kroger",
            "aldi",
            "publix",
            "safeway",
            "whole foods",
            "food lion",
            "meijer",
            "grocery",
            "market",
        ],
        "Entertainment": [
            "netflix",
            "hulu",
            "spotify",
            "disney",
            "cinema",
            "theater",
            "movie",
            "gaming",
            "steam",
            "playstation",
            "xbox",
        ],
        "Shopping": [
            "amazon",
            "target",
            "ebay",
            "etsy",
            "best buy",
            "mall",
            "department store",
        ],
        "Restaurants": [
            "mcdonald",
            "wendy",
            "burger king",
            "taco bell",
            "restaurant",
            "doordash",
            "ubereats",
            "grubhub",
            "starbucks",
        ],
        "Transportation": [
            "shell",
            "speedway",
            "exxon",
            "chevron",
            "bp ",
            "gas",
            "uber",
            "lyft",
            "parking",
        ],
        "Bills & Utilities": [
            "electric",
            "water",
            "internet",
            "phone",
            "utility",
            "insurance",
        ],
    }

    # Start every category at zero.
    category_totals = {
        category_name: 0.0
        for category_name in expense_category_rule_map
    }

    # Expenses that do not match a known category are placed here.
    category_totals["Other Expenses"] = 0.0

    # Examine every transaction.
    for description, amount, transaction_type in zip(
        descriptions,
        amount_values,
        transaction_types,
    ):

        # Ignore transactions that are not expenses.
        if str(transaction_type).strip().lower() != "expense":
            continue

        normalized_description = str(description).strip().lower()

        # Expenses are displayed as positive values.
        expense_amount = abs(float(amount))

        matched_category = None

        # Search the category rules for a matching keyword.
        for category_name, category_keywords in (
            expense_category_rule_map.items()
        ):
            if any(
                keyword in normalized_description
                for keyword in category_keywords
            ):
                matched_category = category_name
                break

        # Use Other Expenses when no rule matches.
        if matched_category is None:
            matched_category = "Other Expenses"

        category_totals[matched_category] += expense_amount

    # Remove categories that had no expenses.
    category_totals = {
        category_name: round(category_total, 2)
        for category_name, category_total in category_totals.items()
        if round(category_total, 2) > 0
    }

    if not category_totals:
        raise ValueError(
            "No expense transactions are available for the pie chart."
        )

    category_labels = list(category_totals.keys())
    category_values = list(category_totals.values())

    # Bright colors for the individual expense categories.
    bright_colors = [
        "#00BFFF",  # Bright blue
        "#FF4D6D",  # Bright pink/red
        "#FFD60A",  # Bright yellow
        "#32CD32",  # Bright green
        "#FF8C00",  # Bright orange
        "#9D4EDD",  # Bright purple
        "#00CED1",  # Bright turquoise
    ]

    # Repeat the color palette if more categories are eventually added.
    pie_colors = [
        bright_colors[index % len(bright_colors)]
        for index in range(len(category_labels))
    ]

    pie_wedges, _ = pie_axis.pie(
        category_values,
        colors=pie_colors,
        startangle=90,
        wedgeprops={
            "edgecolor": "white",
            "linewidth": 1.5,
        },
    )

    return (
        pie_wedges,
        category_labels,
        category_totals,
    )


def style_expense_pie_chart(
    pie_axis,
    pie_wedges,
    category_labels,
    category_totals,
):
    """
    Apply presentation styling to the expense-category pie chart.

    Parameters
    ----------
    pie_axis : matplotlib.axes.Axes
        Axis containing the pie chart.

    pie_wedges : list
        Pie-chart wedges returned by create_expense_pie_chart().

    category_labels : list
        Names of the expense categories represented by the wedges.

    category_totals : dict
        Expense totals for each displayed category.
    """

    if len(pie_wedges) != len(category_labels):
        raise ValueError(
            "Pie wedges and category labels must have matching lengths."
        )

    pie_axis.set_title(
        "Expense Categories",
        fontsize=13,
        fontweight="bold",
        pad=15,
    )

    total_expenses = sum(category_totals.values())

    legend_labels = []

    # Build detailed labels containing category, dollar amount,
    # and percentage of overall expenses.
    for category_name in category_labels:

        category_total = category_totals[category_name]

        category_percentage = (
            category_total / total_expenses
        ) * 100

        legend_labels.append(
            f"{category_name}: "
            f"${category_total:,.2f} "
            f"({category_percentage:.1f}%)"
        )

    pie_axis.legend(
        pie_wedges,
        legend_labels,
        title="Expense Breakdown",
        loc="center left",
        bbox_to_anchor=(1.0, 0.5),
        frameon=False,
        fontsize=9,
        title_fontsize=10,
    )

    # Keep the pie circular regardless of the surrounding figure size.
    pie_axis.set_aspect("equal")

# ============================================================
# TRANSACTION-COUNT CHART FUNCTIONS
# ============================================================
def create_monthly_income_expense_transaction_chart(
    transaction_axis,
    months,
    income_transaction_counts,
    expense_transaction_counts,
    incoming_transfer_counts,
    outgoing_transfer_counts
):
    if transaction_axis is None:
        raise ValueError("A transaction chart axis is required.")

    if len(months) == 0:
        raise ValueError("At least one month is required.")

    (
        income_transaction_counts,
        expense_transaction_counts,
        incoming_transfer_counts,
        outgoing_transfer_counts
    ) = map(np.asarray, (
        income_transaction_counts,
        expense_transaction_counts,
        incoming_transfer_counts,
        outgoing_transfer_counts
    ))

    count_collections = (
        income_transaction_counts,
        expense_transaction_counts,
        incoming_transfer_counts,
        outgoing_transfer_counts
    )

    if any(len(values) != len(months) for values in count_collections):
        raise ValueError(
            "Transaction counts must match the number of months."
        )

    for values in count_collections:
        if (
            values.ndim != 1
            or not np.issubdtype(values.dtype, np.number)
            or not np.isfinite(values).all()
            or (values < 0).any()
            or (values % 1 != 0).any()
        ):
            raise ValueError(
                "Transaction counts must be nonnegative whole numbers."
            )

    if (
        (incoming_transfer_counts > income_transaction_counts).any()
        or (outgoing_transfer_counts > expense_transaction_counts).any()
    ):
        raise ValueError(
            "Transfer counts cannot exceed transaction counts."
        )

    non_transfer_income_counts = (
        income_transaction_counts - incoming_transfer_counts
    )
    non_transfer_expense_counts = (
        expense_transaction_counts - outgoing_transfer_counts
    )

    x_positions = np.arange(len(months))
    bar_width = 0.15
    bar_gap = 0.07

    income_positions = x_positions - ((bar_width + bar_gap) / 2)
    expense_positions = x_positions + ((bar_width + bar_gap) / 2)

    income_transaction_bars = transaction_axis.bar(
        income_positions,
        non_transfer_income_counts,
        width=bar_width,
        color="limegreen",
        alpha=1.0,
        zorder=2,
        label="Income"
    )

    expense_transaction_bars = transaction_axis.bar(
        expense_positions,
        non_transfer_expense_counts,
        width=bar_width,
        color="red",
        alpha=1.0,
        zorder=2,
        label="Expenses"
    )

    has_transfers = (
        (incoming_transfer_counts > 0).any()
        or (outgoing_transfer_counts > 0).any()
    )
    transfer_label = "Transfers" if has_transfers else "_nolegend_"

    incoming_transfer_bars = transaction_axis.bar(
        income_positions,
        incoming_transfer_counts,
        width=bar_width,
        bottom=non_transfer_income_counts,
        color="blue",
        alpha=1.0,
        zorder=3,
        label=transfer_label
    )

    outgoing_transfer_bars = transaction_axis.bar(
        expense_positions,
        outgoing_transfer_counts,
        width=bar_width,
        bottom=non_transfer_expense_counts,
        color="blue",
        alpha=1.0,
        zorder=3,
        label="_nolegend_"
    )

    transaction_axis.set_xticks(x_positions)
    transaction_axis.set_xticklabels(months)
    transaction_axis.set_xlabel("Month")
    transaction_axis.set_ylabel("Transactions")
    transaction_axis.set_title(
        "INCOME vs EXPENSE TRANSACTIONS",
        fontsize=15,
        fontweight="bold",
        color="black"
    )
    transaction_axis.legend(
        loc="lower center",
        bbox_to_anchor=(0.1, -0.35),
        ncol=1,
        fontsize=11,
        frameon=False
    )

    return (
        income_transaction_bars,
        expense_transaction_bars,
        incoming_transfer_bars,
        outgoing_transfer_bars
    )
    
def style_monthly_income_expense_transaction_chart(
    transaction_axis,
    income_transaction_bars,
    expense_transaction_bars,
    incoming_transfer_bars,
    outgoing_transfer_bars
):

    # Define the additional y-axis space.
    y_axis_expansion = 0.08

    # Retrieve and expand the current y-axis limits.
    current_ymin, current_ymax = transaction_axis.get_ylim()
    new_ymax = current_ymax * (1 + y_axis_expansion)

    # Pair each bar collection with a readable label color.
    bar_groups = (
        (income_transaction_bars, "white"),
        (expense_transaction_bars, "white"),
        (incoming_transfer_bars, "white"),
        (outgoing_transfer_bars, "white")
    )

    # Display each nonzero segment's count inside that segment.
    for transaction_bars, label_color in bar_groups:

        for transaction_bar in transaction_bars:

            bar_height = transaction_bar.get_height()

            if bar_height <= 0:
                continue

            bar_center = (
                transaction_bar.get_x()
                + transaction_bar.get_width() / 2
            )

            label_y_position = (
                transaction_bar.get_y()
                + bar_height / 2
            )

            transaction_axis.text(
                bar_center,
                label_y_position,
                f"{bar_height:,.0f}",
                ha="center",
                va="center",
                fontsize=9,
                fontweight="bold",
                color=label_color,
                zorder=4
            )

    # Expand the y-axis to provide room above the bars.
    transaction_axis.set_ylim(
        current_ymin,
        new_ymax
    )

    # Add horizontal grid lines.
    transaction_axis.yaxis.grid(
        True,
        linestyle="--",
        color="grey",
        alpha=0.3
    )

    # Hide the top and right chart borders.
    transaction_axis.spines["top"].set_visible(False)
    transaction_axis.spines["right"].set_visible(False)

    # Create the rounded card surrounding the chart.
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

    # Add the rounded card to the chart.
    transaction_axis.add_patch(card)

    return None
# ============================================================
# TRANSFER CHART FUNCTIONS
# ============================================================
def classify_transfer_subtypes(xlsx_file,description_column_name,transfer_rule_map):

    owned_account_identifier_key = "Owned account transfer"
    personal_transfer_identifier_key = "Personal transfer identifiers"
    unclassified_transfer_identifier_key = "Unclassified transfer identifiers"


    if not isinstance(xlsx_file,pd.DataFrame):
        raise TypeError(
            "Statement data must be provided as a pandas DataFrame."
        )

    if not description_column_name in xlsx_file.columns:
        raise ValueError(
            "The transaction description column could not be found."
        )

    if not isinstance(transfer_rule_map, dict):
        raise TypeError(
            "Transfer rules must be provided as a dictionary."
        )

    required_rule_keys = {
        owned_account_identifier_key,
        personal_transfer_identifier_key,
        unclassified_transfer_identifier_key
    }

    for required_rule_key in required_rule_keys:

        if required_rule_key not in required_rule_keys:
            raise ValueError(
                "Transfer rules do not contain all required transfer categories."
            )

        identifier_collection = transfer_rule_map[required_rule_key]

        if not isinstance(identifier_collection, (list, tuple, set)):
            raise TypeError(
                "Transfer identifiers must be provided as a list, tuple, or set."
            )

        for identifier in identifier_collection:

            if not isinstance(identifier,str):
                raise TypeError(
                    "Each transfer identifier must be a nonempty text value."
                )

            if identifier.strip == "":
                raise ValueError(
                    "Each transfer identifier must be a nonempty text value."
                )

    owned_account_identifiers = transfer_rule_map[owned_account_identifier_key]
    personal_transfer_identifiers = transfer_rule_map[personal_transfer_identifier_key]
    unclassified_transfer_identifiers = transfer_rule_map[unclassified_transfer_identifier_key]

    normalized_descriptions = xlsx_file[description_column_name]
    normalized_descriptions = (
    normalized_descriptions
    .fillna("")
    .astype(str)
    .str.strip()
    .str.lower()
    )

    owned_account_mask = pd.Series(
        False,
        index=xlsx_file.index,
        dtype="bool"
    )
    personal_transfer_mask = pd.Series(
        False,
        index=xlsx_file.index,
        dtype="bool"
    )

    unclassified_transfer_mask = pd.Series(
        False,
        index=xlsx_file.index,
        dtype="bool"
    )

    for identifier in owned_account_identifiers:

        normalized_identifier = identifier.strip().lower()

        current_identifier_mask = normalized_descriptions.str.contains(
        normalized_identifier,
        regex=False,
        na=False
    )

        owned_account_mask = (
        owned_account_mask | current_identifier_mask
    )

    for identifier in personal_transfer_identifiers:

        normalized_identifier = identifier.strip().lower()

        current_identifier_mask = (
            normalized_descriptions.str.contains(
                normalized_identifier,
                regex=False,
                na=False
            )
        )

        personal_transfer_mask = (
            personal_transfer_mask | current_identifier_mask
        )

    for identifier in unclassified_transfer_identifiers:

        normalized_identifier = identifier.strip().lower()

        
        current_identifier_mask = (
            normalized_descriptions.str.contains(
                normalized_identifier,
                regex=False,
                na=False
            )
        )

        unclassified_transfer_mask = (
            unclassified_transfer_mask
            | current_identifier_mask
        )

        transfer_subtypes = pd.Series(
            not_a_transfer,
            index=xlsx_file.index,
            dtype="object"
        )

        transfer_subtypes.loc[
            owned_account_mask
        ] = owned_account_transfer

        transfer_subtypes.loc[
            personal_transfer_mask
            & ~owned_account_mask
        ] = personal_transfer

        transfer_subtypes.loc[
            unclassified_transfer_mask
            & ~owned_account_mask
            & ~personal_transfer_mask
        ] = unclassified_transfer

    return transfer_subtypes

# ============================================================
# SHARED CHART STYLING FUNCTIONS
# ============================================================
def round_bar_tops(chart_axis, bars,):

        # Define the vertical and horizontal rounding proportions.
    vertical_radius_percentage = 0.02
    horizontal_radius_percentage = 0.25

    # Retrieve the current lower and upper limits of the y-axis.
    current_y_min, current_y_max = chart_axis.get_ylim()

    # Calculate the complete visible range of the y-axis.
    y_axis_range = current_y_max - current_y_min

    # Replace each standard bar with a custom rounded bar.
    for bar in bars:

        # Retrieve the current bar's position and dimensions.
        bar_x = bar.get_x()
        bar_y = bar.get_y()
        bar_width = bar.get_width()
        bar_height = bar.get_height()

        # Skip bars that do not have a positive height.
        if bar_height <= 0:
            continue

        # Calculate the horizontal radius using the bar's width.
        horizontal_radius = (
            bar_width * horizontal_radius_percentage
        )

        # Calculate the vertical radius using the visible y-axis range.
        calculated_vertical_radius = (
            y_axis_range * vertical_radius_percentage
        )

        # Limit the vertical radius to half of the bar's height.
        maximum_vertical_radius = bar_height / 2

        # Use the calculated radius when it fits within the bar.
        if calculated_vertical_radius < maximum_vertical_radius:
            vertical_radius = calculated_vertical_radius

        # Use the maximum radius when the calculated radius is too large.
        else:
            vertical_radius = maximum_vertical_radius

        # Preserve the original bar's color and layer position.
        bar_color = bar.get_facecolor()
        bar_zorder = bar.get_zorder()

        # Define the points used to construct the rounded bar shape.
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

        # Define how the path moves between the rounded bar's points.
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

        # Create the path representing the rounded bar.
        rounded_bar_path = MplPath(
            path_vertices,
            path_codes
        )

        # Create the visible patch using the rounded bar path.
        rounded_bar = PathPatch(
            rounded_bar_path,
            facecolor=bar_color,
            edgecolor="none",
            zorder=bar_zorder
        )

        # Hide the original rectangular bar.
        bar.set_visible(False)

        # Add the rounded replacement bar to the chart.
        chart_axis.add_patch(
            rounded_bar
        )

    # Finish the function without returning a value.
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
    expense_transaction_counts,
    incoming_transfer_counts,
    outgoing_transfer_counts
):

     # Determine the financial health status and savings rate.
    financial_health, savings_rate = determine_financial_health(
        total_income,
        total_expenses
    )

    # Create the financial report figure.

    report_figure = plt.figure(figsize=(14, 9))

    # Format the beginning and ending dates for the report.
    formatted_start_date = start_date.strftime("%B %d, %Y")
    formatted_end_date = end_date.strftime("%B %d, %Y")

    # Create the reporting-period text.
    report_period = (
        f"Reporting Period: "
        f"{formatted_start_date} - {formatted_end_date}"
    )

    # Add the program title at the top of the report.
    report_figure.suptitle(
        program_title,
        fontsize=23,
        fontweight="bold",
        color="Black"
    )

    # Display the reporting period below the program title.
    report_figure.text(
        0.5,
        0.9,
        report_period,
        ha="center",
        fontsize=15
    )

    # Create the grid used to organize the report sections.
    report_layout = report_figure.add_gridspec(
        4,
        2,
        height_ratios=[0.2, 1.0, 0.35, 1.6]
    )

    # Create the axis for the financial summary banner.
    banner_axis = report_figure.add_subplot(
        report_layout[0, :]
    )

    # Create the axis for the financial summary table.
    financial_summary = report_figure.add_subplot(
        report_layout[1, :]
    )

    # Create the axis for the financial health summary.
    financial_health_axis = report_figure.add_subplot(
        report_layout[2, :]
    )

    # Create the axis for the monthly income and expense chart.
    income_axis = report_figure.add_subplot(
        report_layout[3, 0]
    )

    # Create the axis for the monthly transaction chart.
    transaction_axis = report_figure.add_subplot(
        report_layout[3, 1]
    )

    # Hide the financial summary axis lines and tick marks.
    financial_summary.axis("off")

    # Set the background color of the financial summary banner.
    banner_axis.set_facecolor(
        "darkblue"
    )

    # Remove the banner's x-axis and y-axis tick marks.
    banner_axis.set_xticks([])
    banner_axis.set_yticks([])

    # Add the financial summary title to the banner.
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

    # Prepare the values displayed in the financial summary table.
    financial_summary_data = [
        ["Transactions", transaction_count],
        ["Total Income", f"${total_income:,.2f}"],
        ["Total Expenses", f"${total_expenses:,.2f}"],
        ["Net Balance", f"${net_balance:,.2f}"]
    ]

    # Create the financial summary table.
    financial_table = financial_summary.table(
        cellText=financial_summary_data,
        colLabels=["Category", "Amount"],
        loc="center"
    )

    # Apply the financial table styling.
    style_financial_table(
        financial_table
    )

    # Create the financial health summary.
    create_financial_health_summary(
        financial_health_axis,
        financial_health,
        savings_rate
    )

    # Create the monthly income and expense chart.
    income_bars, expense_bars = (
        create_monthly_income_expenses_chart(
            income_axis,
            months,
            income_totals,
            expense_totals
        )
    )
   
    # Apply the monthly income and expense chart styling.
    style_monthly_income_expenses_chart(
        income_axis,
        income_bars,
        expense_bars
    )

    # Create the monthly income and expense transaction chart.
    (
    income_transaction_bars,
    expense_transaction_bars,
    incoming_transfer_bars,
    outgoing_transfer_bars
    ) = create_monthly_income_expense_transaction_chart(
        transaction_axis,
        months,
        income_transaction_counts,
        expense_transaction_counts,
        incoming_transfer_counts,
        outgoing_transfer_counts
    )

    # Apply the monthly transaction chart styling.
    style_monthly_income_expense_transaction_chart(
        transaction_axis,
        income_transaction_bars,
        expense_transaction_bars,
        incoming_transfer_bars,
        outgoing_transfer_bars
    )

    round_bar_tops(
        income_axis,
        income_bars
    )

    round_bar_tops(
        income_axis,
        expense_bars
    )

    # Round only the top segment of each Income stack.
    for base_bar, transfer_bar in zip(
        income_transaction_bars,
        incoming_transfer_bars
    ):
        if transfer_bar.get_height() > 0:
            round_bar_tops(
                transaction_axis,
                [transfer_bar]
            )
        else:
            round_bar_tops(
                transaction_axis,
                [base_bar]
            )

    # Round only the top segment of each Expense stack.
    for base_bar, transfer_bar in zip(
        expense_transaction_bars,
        outgoing_transfer_bars
    ):
        if transfer_bar.get_height() > 0:
            round_bar_tops(
                transaction_axis,
                [transfer_bar]
            )
        else:
            round_bar_tops(
                transaction_axis,
                [base_bar]
            )
    
        # Adjust the spacing between the report sections.
        report_figure.subplots_adjust(
            top=0.84,
            bottom=0.18,
            hspace=0.35,
            wspace=0.30
        )

        # Adjust the final spacing around the completed report.
        report_figure.subplots_adjust(
            top=0.84,
            bottom=0.13,
            hspace=0.55,
            wspace=0.30
        )

    # Display the completed financial report.
    plt.show()

    # Return the completed report figure.
    return report_figure

# ============================================================
# REPORT EXPORT FUNCTIONS
# ============================================================
def save_financial_report(report_figure):

    # Continue asking until the user provides a valid save choice.
    while True:

        # Ask the user whether the financial report should be saved.
        save_choice = input(
            "Would you like to save this chart as an image? (Y/N): "
        )

        # Begin the save process when the user enters Y.
        if save_choice.upper() == "Y":

            # Continue asking until the user provides a valid file name.
            while True:

                # Ask for the file name and remove surrounding spaces.
                file_name = input("Please Enter The File Name: ")
                file_name = file_name.strip()

                # Display an error when the user enters an empty file name.
                if file_name == "":
                    print("Must Enter A Valid Input.")
                    continue

                # Create and save the financial report image.
                else:
                    financial_report_file_name = (
                        file_name + "_financial_report.png"
                    )

                    # Save the report figure using the completed file name.
                    report_figure.savefig(
                        financial_report_file_name
                    )

                    # Confirm that the financial report was saved.
                    print(
                        "Charts have been saved successfully."
                    )

                    # Finish the function after saving the report.
                    return

        # End the save process without saving when the user enters N.
        elif save_choice.upper() == "N":
            break

        # Display an error when the user enters an unsupported choice.
        else:
            print(
                "The input is invalid."
            )

    # Finish the function without saving the report.
    return
# ============================================================
# MAIN
# ============================================================
def main():

       # Display the program's welcome screen.
        display_welcome_screen()

        # Open the file dialog and retrieve the selected statement file.
        selected_file = select_xlsx_file()

        # Stop the program when the user does not select a file.
        if selected_file is None:
            print(no_file_selected_error)
            return

        # Attempt to process the statement and create the financial report.
        try:
            # Validate the selected statement file.
            xlsx_path = validate_xlsx_file(
                selected_file
            )

            # Open the validated statement file.
            xlsx_file = open_xlsx(
                xlsx_path
            )

            # Stop the program when the statement cannot be opened.
            if xlsx_file is None:
                return

            # Identify the column containing the transaction dates.
            date_column_name = identify_date_column(
                xlsx_file
            )

            # Identify the column containing the transaction descriptions.
            description_column_name = (
                identify_description_column(
                    xlsx_file
                )
            )

            # Determine the beginning and ending dates of the statement.
            start_date, end_date = determine_date_range(
                xlsx_file,
                date_column_name
            )

            # Calculate the primary financial totals and classify the transactions.
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

            # Create an empty collection for user-provided account identifiers.
            user_owned_account_identifiers = []

            # Create the rules used to identify transfer subtypes.
            transfer_rule_map = create_transfer_rule_map(
                user_owned_account_identifiers
            )

            # Classify the transfer subtype of each transaction.
            transfer_subtypes = classify_transfer_subtypes(
                xlsx_file,
                description_column_name,
                transfer_rule_map
            )

            # Use the default category identifiers.
            user_category_identifiers = None

            # Create the rules used to categorize transactions.
            category_rule_map = create_category_rule_map(
                user_category_identifiers
            )

            # Assign a financial category to each transaction.
            transaction_categories = (
                categorize_transactions(
                    xlsx_file,
                    description_column_name,
                    transaction_types,
                    transfer_subtypes,
                    category_rule_map
                )
            )

            # Calculate the monthly financial totals and transaction counts.
            (
                months,
                income_totals,
                expense_totals,
                income_transaction_counts,
                expense_transaction_counts,
                incoming_transfer_counts,
                outgoing_transfer_counts
            ) = calculate_monthly_summary(
                xlsx_file,
                date_column_name,
                amount_values,
                transaction_types,
                transfer_subtypes
            )

            # Calculate the income and expense totals for each category.
            (
                income_category_totals,
                expense_category_totals
            ) = calculate_category_totals(
                amount_values,
                transaction_types,
                transaction_categories
            )

            # Create the completed financial report.
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
                expense_transaction_counts,
                incoming_transfer_counts,
                outgoing_transfer_counts
            )

            # Ask the user whether the financial report should be saved.
            save_financial_report(
                report_figure
            )

        # Display a user-friendly message when an error occurs.
        except Exception as error:
            print(error)

if __name__ == "__main__":
    main()