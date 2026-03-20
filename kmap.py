"""
Elijah Hewlett
Task 2
"""
from functools import lru_cache

# implicant = (pattern: int, mask: int, cells: frozenset[int])
#   pattern — the fixed bit values that survive simplification
#   mask    — bitmask of positions where variables cancelled out (don't-cares)
#   cells   — truth table row indices this implicant covers

# gray code keeps only one bit changing between neighbors
KMAP_ORDERING = {1: [0,1], 2:[0,1,3,2]}

# map variable count to how many variables go on each axis
# row holds the left side count, col holds the top
KMAP_LAYOUT = {
    2: {"row": 1, "col": 1},
    3: {"row": 1, "col": 2},
    4: {"row": 2, "col": 2},
}

def kmap_layout(num_var):
    # look up the axis split and gray code order for this variable count
    if num_var not in KMAP_LAYOUT:
        raise ValueError(f"Kmap accepts 2-4 variables. You gave {num_var}")
    layout = KMAP_LAYOUT[num_var]
    rows = layout["row"]
    cols = layout["col"]

    return rows, cols, KMAP_ORDERING[rows], KMAP_ORDERING[cols]

def extract_bit(value, bit_pos):
    # pull one bit out of value at the given position
    return (value >> bit_pos) & 1


@lru_cache(maxsize=None)
def group_templates(num_vars):
    # precompute every wrapped power-of-two rectangle for this kmap size once
    row_bits, col_bits, row_seq, col_seq = kmap_layout(num_vars)
    num_rows = len(row_seq)
    num_cols = len(col_seq)

    templates = set()
    for k_row in range(row_bits + 1):
        for k_col in range(col_bits + 1):
            row_size = 1 << k_row
            col_size = 1 << k_col
            if row_size * col_size > (1 << num_vars):
                continue
            for row_start in range(num_rows):
                for col_start in range(num_cols):
                    cells = set()
                    for dr in range(row_size):
                        row_val = row_seq[(row_start + dr) % num_rows]
                        for dc in range(col_size):
                            col_val = col_seq[(col_start + dc) % num_cols]
                            cells.add((row_val << col_bits) | col_val)
                    templates.add(frozenset(cells))

    return tuple(sorted(templates, key=lambda group: (-len(group), tuple(sorted(group)))))


def row_to_bits(row_index, num_vars):
    # convert a row index into its input bits starting from the most significant
    # example: index 5 with 3 vars gives (1, 0, 1)
    bits = []
    for var_index in range(num_vars):
        bit_pos = num_vars - 1 - var_index
        bits.append(extract_bit(row_index, bit_pos))
    return tuple(bits)


@lru_cache(maxsize=None)
def row_bits_table(num_vars):
    # cache the full index-to-bits lookup table for each supported size
    return tuple(row_to_bits(row_index, num_vars) for row_index in range(1 << num_vars))


def minterm_label(bits, variables):
    # build the minterm label — plain variable for 1, complement for 0
    return "".join(var if bit else var + "'" for var, bit in zip(variables, bits))


def maxterm_label(bits, variables):
    # build the maxterm label — plain variable for 0, complement for 1
    literals = [var if bit == 0 else var + "'" for var, bit in zip(variables, bits)]
    return "(" + " + ".join(literals) + ")"


# build the full canonical SOP or POS expression and collect minterms and maxterms
def build_canonical(table, form):
    minterms = table.get_minterms()
    maxterms = table.get_maxterms()
    bits_lookup = row_bits_table(table.num_variables)

    if form == "SOP":
        terms = []
        for minterm_index in minterms:
            bits = bits_lookup[minterm_index]
            terms.append(minterm_label(bits, table.variables))
        canonical = " + ".join(terms) if terms else "0"
    else:
        terms = []
        for maxterm_index in maxterms:
            bits = bits_lookup[maxterm_index]
            terms.append(maxterm_label(bits, table.variables))
        canonical = "".join(terms) if terms else "1"

    return canonical, minterms, maxterms


def group_to_implicant(group):
    # convert a group of cells into a pattern and mask
    indices = sorted(group)
    first = indices[0]
    mask = 0
    for other_index in indices[1:]:
        mask |= first ^ other_index
    pattern = first & ~mask
    return pattern, mask, frozenset(group)


def implicant_literal_count(implicant, num_vars):
    # count how many variables remain after the mask removes the don't-cares
    _, mask, _ = implicant
    return num_vars - mask.bit_count()


def implicant_sort_key(implicant, num_vars):
    # sort by largest group first then fewest literals
    pattern, mask, group = implicant
    return (-len(group), implicant_literal_count(implicant, num_vars), pattern, mask, tuple(sorted(group)))


def exact_cover_search(candidates, uncovered, num_vars):
    # find the smallest set of groups that covers all remaining active cells
    # uses an iterative depth-first stack instead of recursion
    candidate_list = sorted(candidates, key=lambda implicant: implicant_sort_key(implicant, num_vars))
    coverage = {}
    for implicant in candidate_list:
        for cell_index in implicant[2] & uncovered:
            coverage.setdefault(cell_index, []).append(implicant)

    best_solution = None
    best_score = None

    # each entry holds the current search state: (remaining cells, chosen implicants, literal count)
    stack = [(set(uncovered), [], 0)]

    while stack:
        remaining, chosen, literal_total = stack.pop()

        # all cells covered — check if this is the best solution so far
        if not remaining:
            score = (len(chosen), literal_total)
            if best_score is None or score < best_score:
                best_score = score
                best_solution = list(chosen)
            continue

        # prune paths already as expensive as the best known solution
        if best_score is not None and (len(chosen), literal_total) >= best_score:
            continue

        # pick the cell with the fewest options first to find dead ends faster
        most_constrained = min(remaining, key=lambda cell_index: len(coverage.get(cell_index, ())))
        options = coverage.get(most_constrained, ())
        if not options:
            continue

        ordered_options = sorted(
            options,
            key=lambda implicant: (
                -len(implicant[2] & remaining),
                implicant_literal_count(implicant, num_vars),
                implicant_sort_key(implicant, num_vars),
            ),
        )

        # push in reverse order so the best option sits on top of the stack (LIFO)
        for implicant in reversed(ordered_options):
            stack.append((
                remaining - implicant[2],
                chosen + [implicant],
                literal_total + implicant_literal_count(implicant, num_vars),
            ))

    # best_solution stays None if a cell had no covering implicant — returns empty list
    return best_solution or []


def remove_redundant_implicants(outputs, implicants, num_vars, form):
    # final cleanup pass: if dropping an implicant keeps the function correct,
    # leave it out of the printed result.
    minimal = list(implicants)
    changed = True
    while changed:
        changed = False
        for index in range(len(minimal)):
            candidate = minimal[:index] + minimal[index + 1:]
            if validate(outputs, candidate, num_vars, form)["passed"]:
                minimal = candidate
                changed = True
                break
    return minimal


# find all valid K-Map groups for the active cells and pick the smallest cover
def kmap_groups(table, active_indices):
    # active cells are the 1s for SOP or 0s for POS

    active_set = set(active_indices)

    # only keep the precomputed rectangles whose cells are all active
    valid_groups = [
        template
        for template in group_templates(table.num_variables)
        if template <= active_set
    ]

    # drop any group that fits entirely inside a larger one
    sorted_groups = sorted(valid_groups, key=len, reverse=True)
    prime_groups = []
    for i, group in enumerate(sorted_groups):
        is_subset_of_larger = False
        for larger_group in sorted_groups[:i]:
            if group < larger_group:
                is_subset_of_larger = True
                break
        if not is_subset_of_larger:
            prime_groups.append(group)

    # convert each prime group into a pattern and mask
    implicants = [group_to_implicant(group) for group in prime_groups]
    implicants.sort(key=lambda implicant: implicant_sort_key(implicant, table.num_variables))

    # pick essential groups first — forced when a cell has only one option
    coverage = {}
    for implicant in implicants:
        for cell_index in implicant[2]:
            coverage.setdefault(cell_index, []).append(implicant)

    selected = []
    covered = set()
    for cell_index in active_set:
        if len(coverage[cell_index]) == 1:
            only_implicant = coverage[cell_index][0]
            if only_implicant not in selected:
                selected.append(only_implicant)
                covered |= only_implicant[2]

    # cover what's left using exact search to keep the expression as short as possible
    remaining = active_set - covered
    if remaining:
        candidate_implicants = [
            implicant
            for implicant in implicants
            if implicant not in selected and implicant[2] & remaining
        ]
        selected.extend(exact_cover_search(candidate_implicants, remaining, table.num_variables))

    return sorted(selected, key=lambda implicant: implicant_sort_key(implicant, table.num_variables))


def implicant_to_term(implicant, variables, form):
    # turn an implicant into a readable Boolean term
    pattern, mask, _ = implicant
    num_vars = len(variables)
    parts = []
    for var_index, var in enumerate(variables):
        bit_pos = num_vars - 1 - var_index
        if mask & (1 << bit_pos):
            continue                    # this variable cancelled out, skip it
        bit = extract_bit(pattern, bit_pos)
        if form == "SOP":
            # plain variable for 1, complement for 0
            parts.append(var if bit == 1 else var + "'")
        else:
            # plain variable for 0, complement for 1
            parts.append(var if bit == 0 else var + "'")
    if not parts:
        return "1" if form == "SOP" else "0"
    if form == "SOP":
        return "".join(parts)
    if len(parts) == 1:
        # a single literal does not need clause parentheses in POS output
        return parts[0]
    return "(" + " + ".join(parts) + ")"


def format_expression(terms, form):
    # join all terms into the final expression, sort so output stays consistent
    if not terms:
        return "0" if form == "SOP" else "1"
    sorted_terms = sorted(terms, key=lambda t: (len(t), t))
    return " + ".join(sorted_terms) if form == "SOP" else "".join(sorted_terms)


# arrange truth table values into a K-Map grid using Gray-code ordering
def build_kmap(table):
    row_bits, col_bits, row_seq, col_seq = kmap_layout(table.num_variables)

    grid = []
    for row_code in row_seq:
        cells = []
        for col_code in col_seq:
            # merge row and column codes into the table index
            cell_index = (row_code << col_bits) | col_code
            cells.append({"index": cell_index, "value": table.get_output(cell_index)})
        grid.append({
            "label": format(row_code, f"0{row_bits}b"),
            "cells": cells,
        })

    return {
        "row_vars": table.variables[:row_bits],
        "col_vars": table.variables[row_bits:],
        "row_labels": [format(val, f"0{row_bits}b") for val in row_seq],
        "col_labels": [format(val, f"0{col_bits}b") for val in col_seq],
        "grid": grid,
    }


def sop_implicant_covers(pattern, mask, bits, num_vars):
    # check if this implicant covers the given row
    for var_index in range(num_vars):
        bit_pos = num_vars - 1 - var_index
        if mask & (1 << bit_pos):
            continue                            # don't-care, skip
        if extract_bit(pattern, bit_pos) != bits[var_index]:
            return False                        # mismatch, row not covered
    return True


# In POS, a clause like (A + B') is satisfied when at least one literal is true.
# A literal is true when the input bit does NOT match the stored pattern bit —
# because the pattern records the maxterm value (0 = uncomplemented, 1 = complemented).
def pos_clause_satisfied(pattern, mask, bits, num_vars):
    # check if this clause is satisfied for the given row
    # one true literal is enough to satisfy the whole clause
    for var_index in range(num_vars):
        bit_pos = num_vars - 1 - var_index
        if mask & (1 << bit_pos):
            continue                            # this variable isn't in the clause, skip
        if extract_bit(pattern, bit_pos) != bits[var_index]:
            return True                         # found a true literal, clause is satisfied
    return False


# verify the simplified expression matches the original truth table row by row
def validate(outputs, implicants, num_vars, form):
    # check every row against the simplified expression
    mismatches = []
    bits_lookup = row_bits_table(num_vars)

    for row_index, expected in enumerate(outputs):
        bits = bits_lookup[row_index]

        if form == "SOP":
            # output is 1 if any implicant covers this row
            computed = 0
            for pattern, mask, _ in implicants:
                if sop_implicant_covers(pattern, mask, bits, num_vars):
                    computed = 1
                    break
        else:
            # output drops to 0 if any clause fails
            computed = 1
            for pattern, mask, _ in implicants:
                if not pos_clause_satisfied(pattern, mask, bits, num_vars):
                    computed = 0
                    break

        if computed != expected:
            mismatches.append({"index": row_index, "inputs": bits, "expected": expected, "computed": computed})

    return {"passed": not mismatches, "total": len(outputs), "mismatches": mismatches}


def solve(table, form):
    # run the full solve: build canonical form, group the kmap, then validate
    canonical, minterms, maxterms = build_canonical(table, form)
    active_indices = minterms if form == "SOP" else maxterms
    active_set = set(active_indices)

    if not active_indices:
        # no active cells, output is always 0 or 1
        selected_implicants = []
        simplified_str = "0" if form == "SOP" else "1"
        groups = []

    elif len(active_indices) == (1 << table.num_variables):
        # every cell is active, the function is always true or always false
        selected_implicants = [(0, (1 << table.num_variables) - 1, frozenset(active_indices))]
        simplified_str = "1" if form == "SOP" else "0"
        groups = []

    else:
        # normal case, group the active cells on the kmap
        selected_implicants = kmap_groups(table, active_indices)
        selected_implicants = remove_redundant_implicants(
            table.outputs, selected_implicants, table.num_variables, form
        )

        terms = []
        for implicant in selected_implicants:
            terms.append(implicant_to_term(implicant, table.variables, form))

        simplified_str = format_expression(terms, form)
        groups = []
        for implicant, term_text in zip(selected_implicants, terms):
            groups.append(
                {
                    "covered": sorted(implicant[2] & active_set),
                    "term": term_text,
                    "size": len(implicant[2]),
                }
            )

    kmap = build_kmap(table)
    validation = validate(table.outputs, selected_implicants, table.num_variables, form)

    return {
        "form": form,
        "canonical": canonical,
        "minterms": minterms,
        "maxterms": maxterms,
        "simplified_str": simplified_str,
        "groups": groups,
        "kmap": kmap,
        "validation": validation,
    }


# ask the user to choose SOP or POS, with a hint based on output distribution
def select_form(table=None):
    # ask which Boolean form to use, with an optional hint based on output distribution
    print("\nSelect Boolean form:")
    print("  1. Sum of Products (SOP)")
    print("  2. Product of Sums (POS)")
    if table is not None:
        ones  = len(table.get_minterms())
        zeros = len(table.get_maxterms())
        if zeros > ones:
            print("  (More 0s than 1s — POS may give fewer terms.)")
        elif ones > zeros:
            print("  (More 1s than 0s — SOP may give fewer terms.)")
    while True:
        choice = input("* ").strip()
        if choice == "1":
            return "SOP"
        if choice == "2":
            return "POS"
        print("  Enter 1 or 2.")
