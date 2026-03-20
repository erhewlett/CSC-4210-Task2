import csv


class TruthTable:

    def __init__(self, variables, outputs, output_name="F"):
        # store everything then run validation
        self.variables = [str(variable_name).strip() for variable_name in variables]
        self.output_name = output_name.strip() or "F"
        self.outputs = list(outputs)
        self.num_variables = len(self.variables)
        self.num_rows = len(self.outputs)
        self.validate()

    # check variable names, row count, and output values before anything else runs
    def validate(self):
        # catch bad input before anything else runs
        if not (2 <= self.num_variables <= 4):
            raise ValueError(
                f"This program supports 2 to 4 input variables. Got {self.num_variables}."
            )

        for variable_name in self.variables:
            if not variable_name.isidentifier():
                raise ValueError(
                    f"Variable name '{variable_name}' must start with a letter and contain only letters, digits, or underscores."
                )

        if len(set(self.variables)) != len(self.variables):
            raise ValueError("Variable names must be unique.")

        expected_rows = 1 << self.num_variables
        if self.num_rows != expected_rows:
            raise ValueError(
                f"Expected {expected_rows} rows for {self.num_variables} variables, got {self.num_rows}."
            )

        for output_value in self.outputs:
            if output_value not in (0, 1):
                raise ValueError("All output values must be 0 or 1.")

    def index_to_bits(self, index):
        # row index to bit tuple, e.g. index 5 with 3 vars gives (1, 0, 1)
        return tuple((index >> bit_pos) & 1 for bit_pos in range(self.num_variables - 1, -1, -1))

    def get_output(self, index):
        return self.outputs[index]

    def get_minterms(self):
        # collect all rows where the output is 1
        minterms = []
        for row_index, output_value in enumerate(self.outputs):
            if output_value == 1:
                minterms.append(row_index)
        return minterms

    def get_maxterms(self):
        # collect all rows where the output is 0
        maxterms = []
        for row_index, output_value in enumerate(self.outputs):
            if output_value == 0:
                maxterms.append(row_index)
        return maxterms

    @classmethod
    def from_rows(cls, variables, rows, output_name="F"):
        # build the table from a list of row dictionaries
        variables = [str(variable_name).strip() for variable_name in variables]

        num_vars = len(variables)
        if not (2 <= num_vars <= 4):
            raise ValueError(f"This program supports 2 to 4 input variables. Got {num_vars}.")

        seen_inputs = set()
        outputs = [0] * (1 << num_vars)

        for row_number, row_data in enumerate(rows):
            input_bits = tuple(row_data["inputs"])
            output_value = row_data["output"]

            if len(input_bits) != num_vars:
                raise ValueError(f"Row {row_number}: expected {num_vars} inputs, got {len(input_bits)}.")

            for input_bit in input_bits:
                if input_bit not in (0, 1):
                    raise ValueError(f"Row {row_number}: inputs must be 0 or 1.")

            if output_value not in (0, 1):
                raise ValueError(f"Row {row_number}: output must be 0 or 1.")

            if input_bits in seen_inputs:
                raise ValueError(f"Row {row_number}: duplicate input combination {list(input_bits)}.")

            seen_inputs.add(input_bits)

            # convert the bit pattern into the matching row index
            row_index = 0
            for bit_value in input_bits:
                row_index = row_index * 2 + bit_value
            outputs[row_index] = output_value

        if len(seen_inputs) != (1 << num_vars):
            raise ValueError(
                f"Expected {1 << num_vars} rows for {num_vars} variables, got {len(seen_inputs)}."
            )

        return cls(variables=variables, outputs=outputs, output_name=output_name)

    @staticmethod
    def _default_vars(num_vars):
        # generate default variable names starting from A
        return [chr(ord("A") + i) for i in range(num_vars)]

    # load a truth table from a CSV file
    @staticmethod
    def load_from_csv(filepath):
        # read the csv — first row is the header, last column is the output
        try:
            with open(filepath, newline="", encoding="utf-8-sig") as csv_file:
                csv_rows = list(csv.reader(csv_file))
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: '{filepath}'")

        if len(csv_rows) < 2:
            raise ValueError("CSV must have a header row and at least one data row.")

        header = [column_name.strip() for column_name in csv_rows[0]]
        if len(header) < 2 or any(column_name == "" for column_name in header):
            raise ValueError(
                "CSV header must name all input variables and the output. Example: A,B,C,F"
            )

        variables = header[:-1]
        output_name = header[-1]
        expected_cols = len(variables) + 1
        rows = []

        for row_number, raw_row in enumerate(csv_rows[1:], start=1):
            # skip blank lines
            if all(cell_text.strip() == "" for cell_text in raw_row):
                continue

            cleaned_row = [cell.strip() for cell in raw_row]

            if len(cleaned_row) != expected_cols:
                raise ValueError(f"Row {row_number}: expected {expected_cols} columns, got {len(cleaned_row)}.")

            try:
                values = [int(cell_text) for cell_text in cleaned_row]
            except ValueError:
                raise ValueError(f"Row {row_number}: all values must be 0 or 1.")

            rows.append({"inputs": values[:-1], "output": values[-1]})

        return TruthTable.from_rows(variables=variables, rows=rows, output_name=output_name)

    # walk the user through entering a truth table manually
    @staticmethod
    def load_from_console(num_vars=None):
        # walk the user through building a truth table manually
        print("\nConsole Input Mode")

        if num_vars is None:
            while True:
                try:
                    raw_count = input("How many input variables? (2, 3, or 4): ").strip()
                    num_vars = int(raw_count)
                    if 2 <= num_vars <= 4:
                        break
                    print("  Must be 2, 3, or 4.")
                except ValueError:
                    print("  Enter a whole number.")
        elif not isinstance(num_vars, int) or not (2 <= num_vars <= 4):
            raise ValueError("Console input supports 2 to 4 input variables.")

        default_names = TruthTable._default_vars(num_vars)
        while True:
            print(f"Variable names separated by spaces (press Enter for defaults: {' '.join(default_names)}):")
            entered_variable_names = input("* ").strip().split()
            variables = entered_variable_names if entered_variable_names else default_names
            if len(variables) == num_vars:
                break
            print(f"  Expected {num_vars} name(s), got {len(variables)}. Try again.")

        raw_output_name = input("Output variable name (press Enter for default: F): ").strip()
        output_name = raw_output_name if raw_output_name else "F"

        total_rows = 1 << num_vars

        # show the full input table so the user knows the row order
        header_str = " | ".join(variables) + f" | {output_name}"
        separator = "-" * len(header_str)
        print(f"\n{header_str}")
        print(separator)
        for row_index in range(total_rows):
            bits_str = " | ".join(
                str((row_index >> shift) & 1) for shift in range(num_vars - 1, -1, -1)
            )
            print(f"  {bits_str} | -")

        # take all outputs at once and re-prompt if anything is wrong
        while True:
            try:
                raw = input(f"\nEnter all {total_rows} outputs (space-separated): ").strip().split()
                if len(raw) != total_rows:
                    print(f"  Need exactly {total_rows} values, got {len(raw)}. Try again.")
                    continue
                outputs = [int(v) for v in raw]
                if any(v not in (0, 1) for v in outputs):
                    print("  All values must be 0 or 1. Try again.")
                    continue
                break
            except ValueError:
                print("  Invalid input. Use only 0s and 1s.")

        return TruthTable(variables=variables, outputs=outputs, output_name=output_name)

    @staticmethod
    def load_input():
        # handle the input menu and retry loop in one place
        while True:
            print("\nSelect input method:")
            print("  1. CSV file")
            print("  2. Console input")

            choice = input("* ").strip()
            if choice == "1":
                filename = input("  File path: ").strip()
                try:
                    return TruthTable.load_from_csv(filename)
                except (ValueError, FileNotFoundError) as error:
                    print(f"\n  [Error] {error}  Try again.\n")
                    continue

            if choice == "2":
                try:
                    return TruthTable.load_from_console()
                except (ValueError, KeyboardInterrupt):
                    print("\n  Input cancelled.  Try again.\n")
                    continue

            print("  Enter 1 or 2.")


