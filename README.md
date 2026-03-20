# Karnaugh Map Boolean Simplifier

**Student:** Elijah Hewlett
**Course:** Computer Architecture 
**Assignment:** Task 2



#Overview

A Python command-line program that takes a truth table and simplifies the Boolean expression using a Karnaugh map.

The program builds the canonical SOP or POS form, finds valid K-map groupings, generates a simplified expression, then verifies the result matches the original truth table.

Supports 2, 3, or 4 input variables.



How It Works

1. Load a truth table from a CSV file or enter it manually in the terminal.
2. Validate the table (correct row count, unique input combinations, 0/1 outputs only).
3. Choose SOP (Sum of Products) or POS (Product of Sums).
4. Build the canonical Boolean expression and list minterms or maxterms.
5. Arrange values into a K-map using Gray-code ordering.
6. Find valid power-of-two groups, including wraparound groups.
7. Convert the selected groups into a simplified Boolean expression.
8. Validate the simplified expression against every row of the original table.


Project Structure

- `main.py` — entry point, handles the user interaction loop
- `truth_table.py` — truth table validation, CSV loading, and console input
- `kmap.py` — K-map layout, grouping, simplification, and validation logic
- `truth_table_helper.py` — terminal output for the truth table, K-map, and results




Requirements

Python 3. No external libraries — standard library only.



How To Run

```bash
python3 main.py
```

The program will ask you to choose an input method, load the truth table, pick SOP or POS, then display the truth table, canonical form, K-map, group overlay, simplified expression, and validation result. It will offer to run again when done.


CSV Format

The first row is the header. Input variables come first, output variable last. All values must be 0 or 1.

```
A,B,C,F
0,0,0,0
0,0,1,1
0,1,0,1
0,1,1,1
1,0,0,0
1,0,1,1
1,1,0,1
1,1,1,1
```

Rules:
- 2 to 4 input variables only
- Every possible input combination must appear exactly once
- Variable names must be unique



Example Output

Running a 3-variable majority function (output is 1 when at least two inputs are 1) in SOP mode:

```
canonical:  A'BC + AB'C + ABC' + ABC
Σm:        3 5 6 7

simplified: F = AB + AC + BC
validation: PASS
```

The K-map display uses Gray-code ordering and prints a numbered group overlay:
- each group is labeled `1`, `2`, `3`, etc.
- overlapping cells show combined labels such as `1+2`
- blank cells are not part of the final cover


