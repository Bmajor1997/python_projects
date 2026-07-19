#Project Name: Personal Spending Analyzer

# ============================================================
# IMPORTS
# ============================================================
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from tkinter import filedialog
import tkinter as tk
import numpy as np
# ============================================================
# APPLICATION INFORMATION
# ============================================================
application_name = "Personal Finance Analyzer"
application_version = "Version 1.0"
program_title = "Personal Finance Analyzer"
# ============================================================
# USER INTERFACE
# ============================================================
divider = "=" * 60
welcome_message = (
    "Welcome!\n\n"
    "This application analyzes bank-exported CSV files and\n"
    "provides financial summaries and visualizations."
)
# ============================================================
# PROMPT MESSAGES
# ============================================================
csv_path_prompt = "Enter the path to your bank CSV: "
# ============================================================
# ERROR MESSAGES
# ============================================================
file_not_found_error = "The selected file could not be found."
no_file_selected_error = "No file path was provided."
invalid_file_type_error = "The selected file is not a CSV file."
empty_file_error = "The selected CSV file is empty."
missing_columns_error = "The CSV file is missing one or more required columns."
invalid_bank_file_error = "The selected file is not a valid bank transaction CSV."
invalid_transaction_data_error = (
    "The transaction data contains invalid values. "
    "Please correct the CSV and try again."
)
csv_open_error = "File could not be opened."
# ============================================================
# FILE DIALOG CONSTANTS
# ============================================================
file_dialog_title = "Select Your Bank CSV File"
csv_file_types = [("CSV Files", "*.csv")]
no_file_selected_message = (
    "No file was selected.\n\n"
    "Please select a bank CSV file to continue."
)
# ============================================================
# HELPER FUNCTIONS
# ============================================================
def display_welcome_screen():

    print(divider)
    print(program_title)
    print(application_version)
    print(divider)
    print(welcome_message)
    print(divider)

def select_csv_file():

    root = tk.Tk()
    root.withdraw()

    selected_file = filedialog.askopenfilename(
        title=file_dialog_title,
        filetypes=csv_file_types
    )

    root.destroy()

    if not selected_file:
        return None

    return selected_file

def validate_csv_file(selected_file):

    csv_path = Path(selected_file)

    if not csv_path.exists():
        raise Exception(no_file_selected_error)

    if csv_path.suffix != ".csv":
        raise Exception(invalid_file_type_error)

    if csv_path.stat().st_size == 0:
        raise Exception(empty_file_error)

def open_csv(csv_path):

    try:
        csv_file = pd.read_csv(csv_path)
    except Exception:
        print(csv_open_error)

def count_transactions(csv_file):

    transaction_count = len(csv_file)

    return transaction_count

def identify_date_column(csv_file):

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
    no_date_column_found_error =" No Date Column Found."
    normalized_columns = csv_file.columns.str.strip().str.lower()


    possible_date_columns = pd.Index(possible_date_column_names)
    matching_columns = normalized_columns.intersection(
        possible_date_columns
    )

    if len(matching_columns) == 0:
        raise ValueError(no_date_column_found_error)

    date_column_name = matching_columns[0]

    return  date_column_name

def determine_date_range(csv_file,date_column_name ):

    # Create error message
    no_dates_found_error = "No Dates Were Found."

    # Retrieve the transaction date column
    date_values = csv_file[date_column_name]

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

def create_monthly_income_expenses_chart(
        months,
        income_totals,
        expense_totals
):

    # CREATE a new figure and axes
    fig, ax = plt.subplots()

    # SET the width of each bar
    bar_width = .30

    # CALCULATE the x-axis positions for each month
    x_positions = np.arange(len(months))

    ax.bar(
        x_positions - (bar_width / 2),
        income_totals,
        width=bar_width,
        label="Income",
        color="green"
    )

    ax.bar(x_positions + (bar_width/2),
           expense_totals,
           width=bar_width,
           label="Expenses",
           color="red"
           )
    ax.set_xticks(x_positions)
    ax.set_xlabel(months)

    ax.set_ylabel("Amount ($)")
    ax.set_title("Monthly Financial Summary")

    ax.legend()

    plt.show()

    return fig

def offer_to_save_chart(chart):

    chart_prompt = "Would you like to save this chart as an image? (Y/N): "
    invalid_save_choice_message = "The input is invalid."
    chart_saved_successfully_message = "Chart has been saved successfully."
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
                    complete_file_name = file_name + ".png"
                    chart.savefig(complete_file_name)
                    print(chart_saved_successfully_message)
                    return

        elif save_choice.upper() == "N":
            break

        else:
            print(invalid_save_choice_message)

    return


def create_monthly_transaction_count_chart():
    pass

def calculate_financial_summary(csv_file):
    pass

def display_financial_summary():
    pass
# ============================================================
# MAIN TEST FUNCTIONS
# ============================================================
# Add for Version 2.0
def create_expense_category_chart():
    pass

# ============================================================
# MAIN
# ============================================================
def main():
    display_welcome_screen()


if __name__ == "__main__":
    main()
