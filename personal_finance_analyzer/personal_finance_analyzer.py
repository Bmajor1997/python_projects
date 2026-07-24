# Project Name: Personal Spending Analyzer
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
application_version = "Beta version 1.0"
program_title = "Personal Finance Analyzer"
application_name = "Financial Summary Report"
# ============================================================
# USER INTERFACE
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
# ============================================================
# MAIN TEST FUNCTIONS
# ============================================================
def display_welcome_screen():

    print(divider)
    print(program_title)
    print(application_version)
    print(divider)
    print(welcome_message)
    print(divider)

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

def open_xlsx(xlsx_path):

    try:
        xlsx_file = pd.read_excel(xlsx_path)
    except Exception:
        print(xlsx_open_error)
        return None

    return xlsx_file

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

    normalized_columns = (
        xlsx_file.columns
        .str.strip()
        .str.lower()
    )

    possible_date_columns = pd.Index(
        possible_date_column_names
    )

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

    normalized_columns = (
        xlsx_file.columns
        .str.strip()
        .str.lower()
    )

    possible_amount_columns = pd.Index(
        possible_amount_column_names
    )

    matching_amount = normalized_columns.intersection(
        possible_amount_columns
    )

    if len(matching_amount) == 0:
        raise ValueError(no_amount_column_found_error)

    matching_column_name = matching_amount[0]

    column_position = normalized_columns.get_loc(
        matching_column_name
    )

    amount_column_name = xlsx_file.columns[column_position]

    return amount_column_name

def count_transactions(xlsx_file):

    transaction_count = len(xlsx_file)

    return transaction_count

def calculate_financial_summary(xlsx_file):

    transaction_count = count_transactions(xlsx_file)
    amount_column_name = identify_amount_column(xlsx_file)

    amount_values = xlsx_file[amount_column_name]

    amount_values =  amount_values.astype(str)
    amount_values = amount_values.str.replace("$", "", regex=False)
    amount_values = amount_values.str.replace(",", "", regex=False)
    amount_values = pd.to_numeric(
        amount_values,
        errors="coerce"
    )
    amount_values = amount_values.dropna()

    total_income = amount_values[amount_values > 0].sum()

    total_expense = amount_values[amount_values < 0].sum()

    net_balance = total_income + total_expense

    return transaction_count,total_income,total_expense,net_balance, amount_values

def calculate_monthly_summary(xlsx_file, date_column_name, amount_values):

    monthly_data = pd.DataFrame({
        "date": xlsx_file[date_column_name],
        "amount": amount_values
    })

    monthly_data["date"] = pd.to_datetime(
        monthly_data["date"],
        errors="coerce"
    )

    monthly_data = monthly_data.dropna(
        subset=["date", "amount"]
    )

    monthly_data["month"] = monthly_data["date"].dt.month_name()

    monthly_income = monthly_data[
        monthly_data["amount"] > 0
        ]

    monthly_expenses = monthly_data[
        monthly_data["amount"] < 0
        ]

    monthly_income = monthly_income.groupby("month")["amount"].sum()
    monthly_expenses = monthly_expenses.groupby("month")["amount"].sum()

    monthly_transactions = monthly_data.groupby("month").size()

    months = monthly_transactions.index.tolist()

    income_totals = monthly_income.tolist()

    expense_totals = monthly_expenses.abs().tolist()

    transaction_counts = monthly_transactions.tolist()

    return months, income_totals, expense_totals, transaction_counts

def create_monthly_income_expenses_chart(
        income_axis,
        months,
        income_totals,
        expense_totals
):

    # SET the width of each bar
    bar_width = 0.15

    # CALCULATE the x-axis positions for each month
    x_positions = np.arange(len(months))

    income_axis.bar(
        x_positions - (bar_width / 2),
        income_totals,
        width=bar_width,
        label="Income",
        color="green"
    )

    income_axis.bar(
        x_positions + (bar_width / 2),
        expense_totals,
        width=bar_width,
        label="Expenses",
        color="red"
    )

    income_axis.set_xticks(x_positions)
    income_axis.set_xticklabels(months)

    income_axis.set_xlabel("Month")
    income_axis.set_ylabel("Amount ($)")
    income_axis.set_title("Monthly Financial Summary")

    income_axis.legend()

def create_monthly_transaction_count_chart(transaction_axis,months,transaction_counts):
    # CALCULATE the x-axis positions for each month

    x_positions = np.arange(len(months))
    bar_width = 0.15

    transaction_axis.bar(
        x_positions,
        transaction_counts,
        width=bar_width,
        color="blue"
    )

    transaction_axis.set_xticks(x_positions)
    transaction_axis.set_xticklabels(months)

    transaction_axis.set_xlabel("Month")
    transaction_axis.set_ylabel("Transactions")
    transaction_axis.set_title("Monthly Transactions")

def style_financial_table():
    pass
def determine_financial_health():
    pass

def create_financial_report(transaction_count,start_date,end_date,total_income,

    total_expenses,net_balance,months,income_totals,expense_totals,transaction_counts):

    # Create report

    report_figure = plt.figure(figsize=(14, 8))

    formatted_start_date = start_date.strftime("%B %d, %Y")
    formatted_end_date = end_date.strftime("%B %d, %Y")

    report_period = (f"Reporting Period: {formatted_start_date} - {formatted_end_date}")

    report_figure.suptitle(program_title, fontsize=23, fontweight="bold", color="Black")
    report_figure.text(0.5, 0.91, application_name, ha = "center", fontsize=18, color="darkblue")
    report_figure.text(0.5, 0.87, report_period, ha = "center", fontsize=15)
    
    report_layout = report_figure.add_gridspec(2,2, height_ratios=[0.7, 1.3])
    income_axis = report_figure.add_subplot(report_layout[1, 0])
    transaction_axis = report_figure.add_subplot(report_layout[1, 1])
    financial_summary = report_figure.add_subplot(report_layout[0, :])
    financial_summary.axis("off")

    report_figure.text(0.5,0.83, "Financial Summary", ha="center", fontsize=16)
   
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
    financial_table.scale(1.0,2.0
                          )
    create_monthly_income_expenses_chart(
        income_axis,
        months,
        income_totals,
        expense_totals
    )

    create_monthly_transaction_count_chart(
        transaction_axis,
        months,
        transaction_counts
    )

    report_figure.subplots_adjust(
        top=0.84,
        hspace=0.40,
        wspace=0.30
    )

    plt.show()

    return report_figure

def save_financial_report(income_expense_chart,transaction_count_chart):

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
                    income_expense_file_name = (
                            file_name + "_income_expenses.png"
                    )

                    transaction_count_file_name = (
                            file_name + "_transaction_count.png"
                    )

                    income_expense_chart.savefig(
                        income_expense_file_name
                    )

                    transaction_count_chart.savefig(
                        transaction_count_file_name
                    )

                    print(chart_saved_successfully_message)
                    return

        elif save_choice.upper() == "N":
            break

        else:
            print(invalid_save_choice_message)

    return

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

        date_column_name = identify_date_column(xlsx_file)

        start_date, end_date = determine_date_range(
            xlsx_file,
            date_column_name
        )

        (
            transaction_count,
            total_income,
            total_expenses,
            net_balance,
            amount_values
        ) = calculate_financial_summary(xlsx_file)

        (
            months,
            income_totals,
            expense_totals,
            transaction_counts
        ) = calculate_monthly_summary(
            xlsx_file,
            date_column_name,
            amount_values
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
            transaction_counts
        )

        save_financial_report(report_figure,)

    except Exception as error:
        print(error)

if __name__ == "__main__":
    main()
