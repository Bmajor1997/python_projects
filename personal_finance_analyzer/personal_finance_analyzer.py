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
application_version = "Beta version 1.0"
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
def style_net_balance_row(financial_table,financial_health):
    
    (
        status_foreground_color,
        status_background_color
    ) = get_financial_health_colors(
        financial_health
    )

    net_balance_row_index = 4
    net_balance_border_width = 1.5

    for column_index in range(0,4):
        
def create_financial_health_summary(financial_health_axis,financial_health,savings_rate):
    
    financial_health_title = "Financial Health"
    status_label = "Status:"
    savings_rate_label = "Savings Rate:"
    unavailable_rate_text = "N/A"

    card_x_position = 0.01
    card_y_position = 0.35
    card_width = .98
    card_height = .8

    common_vertical_position = .68
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
   
def create_monthly_transaction_count_chart(transaction_axis,months,transaction_counts):
    # CALCULATE the x-axis positions for each month

    x_positions = np.arange(len(months))
    bar_width = 0.15

    transaction_bars = transaction_axis.bar(
        x_positions,
        transaction_counts,
        width=bar_width,
        color="blue",
        alpha = 1.0,
        zorder = 2
    )

    transaction_axis.set_xticks(x_positions)
    transaction_axis.set_xticklabels(months)

    transaction_axis.set_xlabel("Month")
    transaction_axis.set_ylabel("Transactions")
    transaction_axis.set_title("MONTHLY TRANSACTIONS",fontsize=15, fontweight="bold", color="black" )

    return transaction_bars

def style_monthly_transaction_count_chart(transaction_axis,transaction_bars):

    label_offset_percentage = 0.02
    y_axis_expansion = 0.08

    current_ymin, current_ymax = transaction_axis.get_ylim()

    expansion_amount = current_ymax * y_axis_expansion
    new_ymax = current_ymax + expansion_amount

    label_offset = current_ymax * label_offset_percentage

    for transaction_bar in transaction_bars:
        bar_height = transaction_bar.get_height()
        bar_center = (transaction_bar.get_x() + transaction_bar.get_width() / 2)
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

    transaction_axis.set_ylim(current_ymin, new_ymax)

    transaction_axis.yaxis.grid(
        True,
        linestyle="--",
        color = "grey",
        alpha=0.3
    )

    transaction_axis.spines["top"].set_visible(False)
    transaction_axis.spines["right"].set_visible(False)
        
    card = FancyBboxPatch(
            (-0.15, -0.32),
            1.17,
            1.47,
            transform=transaction_axis.transAxes,
            boxstyle="round,pad=0.02,rounding_size=0.03",
            facecolor="white",
            edgecolor="lightblue",
            linewidth=1.5,
            clip_on=False,
            zorder=-1
    )

    transaction_axis.add_patch(card)  

    return None

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
    transaction_counts
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
        height_ratios=[0.2, 0.8, 0.35, 1.6]
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

    banner_axis.set_facecolor("darkblue")
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

    style_financial_table(financial_table)

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

    transaction_bars = create_monthly_transaction_count_chart(
        transaction_axis,
        months,
        transaction_counts
    )

    style_monthly_transaction_count_chart(
        transaction_axis,
        transaction_bars
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
        transaction_bars,
    )

    report_figure.subplots_adjust(
        top=0.84,
        bottom=0.18,
        hspace=0.35,
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