"""
Elijah Hewlett
Task 2
"""

from truth_table import TruthTable
from kmap import solve, select_form
from truth_table_helper import print_truth_table, print_results


def main():
    while True:
        # load the truth table from a CSV file or console input
        table = TruthTable.load_input()

        print(f"\nLoaded {table.num_variables} variables: {', '.join(table.variables)}.")
        print(f"{table.num_rows} rows created.")

        # ask the user which Boolean form to use
        form = select_form(table)

        # build the canonical form, group the K-Map, and produce the simplified expression
        result = solve(table, form)

        # print the truth table then all results
        active = result["minterms"] if form == "SOP" else result["maxterms"]
        print_truth_table(table, highlight=active, form=form)
        print_results(result, table)

        again = input("\nRun again? (y/n): ").strip().lower()
        if again != "y":
            break


if __name__ == "__main__":
    main()
