import sys

CELL = 5  # width of each kmap cell


def _box_chars():
    # use double-line box drawing when the terminal encoding can handle it
    encoding = (sys.stdout.encoding or "").lower()
    if "utf" in encoding:
        return {
            "h": "═",
            "v": "║",
            "tl": "╔",
            "tr": "╗",
            "bl": "╚",
            "br": "╝",
            "tj": "╦",
            "bj": "╩",
            "lj": "╠",
            "rj": "╣",
            "cross": "╬",
        }
    return {
        "h": "-",
        "v": "|",
        "tl": "+",
        "tr": "+",
        "bl": "+",
        "br": "+",
        "tj": "+",
        "bj": "+",
        "lj": "+",
        "rj": "+",
        "cross": "+",
    }


# print the truth table with active rows highlighted by minterm or maxterm label
def print_truth_table(table, highlight=None, form="SOP"):
    highlight = set(highlight) if highlight else set()
    prefix = "m" if form == "SOP" else "M"
    header = " | ".join(table.variables) + f" | {table.output_name}"
    print("\nTruth Table")
    print(header)
    print("-" * len(header))
    for row_index in range(table.num_rows):
        bits = table.index_to_bits(row_index)
        row_str = " | ".join(str(bit) for bit in bits) + f" | {table.outputs[row_index]}"
        if row_index in highlight:
            row_str += f"  {prefix}{row_index}"
        print(row_str)


def _kmap_parts(kmap):
    # pull out the axis names and widths needed to align the grid
    row_axis = "".join(kmap["row_vars"])
    col_axis = "".join(kmap["col_vars"])
    lbl_w = max(len(lbl) for lbl in kmap["row_labels"])
    prefix_w = len(row_axis) + 1 + lbl_w + 1
    return row_axis, col_axis, lbl_w, prefix_w


def _kmap_border(prefix_w, num_cols, left, join, right):
    # build one horizontal border row
    box = _box_chars()
    return " " * prefix_w + left + ((box["h"] * CELL) + join) * (num_cols - 1) + (box["h"] * CELL) + right


def _print_kmap_grid(kmap, cell_fn):
    # print the kmap grid, using cell_fn to decide what goes in each cell
    row_axis, col_axis, lbl_w, prefix_w = _kmap_parts(kmap)
    col_labels = kmap["col_labels"]
    num_cols = len(col_labels)

    box           = _box_chars()
    top_border    = _kmap_border(prefix_w, num_cols, box["tl"], box["tj"], box["tr"])
    mid_border    = _kmap_border(prefix_w, num_cols, box["lj"], box["cross"], box["rj"])
    bottom_border = _kmap_border(prefix_w, num_cols, box["bl"], box["bj"], box["br"])
    col_hdr       = " " * prefix_w + "".join(f"{box['v']}{lbl:^{CELL}}" for lbl in col_labels) + box["v"]
    axis_indent   = prefix_w + (CELL + 1) * num_cols // 2 - len(col_axis) // 2
    col_axis_line = " " * axis_indent + col_axis

    print(col_axis_line)
    print(top_border)
    print(col_hdr)
    print(mid_border)

    mid = len(kmap["grid"]) // 2
    for i, row in enumerate(kmap["grid"]):
        # place the row axis label at the middle row
        ra = row_axis if i == mid else " " * len(row_axis)
        line = f"{ra} {row['label']:>{lbl_w}} "
        line += "".join(f"{box['v']}{cell_fn(cell):^{CELL}}" for cell in row["cells"])
        line += box["v"]
        print(line)
        if i != len(kmap["grid"]) - 1:
            print(mid_border)

    print(bottom_border)


def print_kmap(kmap):
    print("\nK-Map")
    _print_kmap_grid(kmap, lambda cell: str(cell["value"]))


def print_kmap_overlay(kmap, groups):
    # map each covered cell to the group number(s) that use it
    cell_labels = {}
    for group_number, group in enumerate(groups, start=1):
        for cell_index in group["covered"]:
            cell_labels.setdefault(cell_index, []).append(str(group_number))

    # show explicit group labels; if multiple groups overlap, join them when
    # they fit in the cell, otherwise fall back to "+"
    def mark(cell):
        labels = cell_labels.get(cell["index"])
        if not labels:
            return ""
        if len(labels) == 1:
            return labels[0]
        joined = "+".join(labels)
        return joined if len(joined) <= CELL else "+"

    print("\nK-Map Group Overlay")
    _print_kmap_grid(kmap, mark)
    print("Legend: blank = not used, numbers = group number, 1+2 = overlap")


# canonical form, k-map, simplified expression, and validation — one concept per line
def print_results(result, table):
    form      = result["form"]
    minterms  = result["minterms"]
    maxterms  = result["maxterms"]
    active    = minterms if form == "SOP" else maxterms
    sigma     = "Σm" if form == "SOP" else "ΠM"
    index_str = " ".join(str(i) for i in active)

    print(f"\ncanonical:  {result['canonical']}")
    print(f"{sigma}:        {index_str}")

    print_kmap(result["kmap"])
    if result["groups"]:
        print_kmap_overlay(result["kmap"], result["groups"])

    print(f"\nsimplified: {table.output_name} = {result['simplified_str']}")

    validation = result["validation"]
    verified   = "PASS" if validation["passed"] else "FAIL"
    print(f"validation: {verified}")
    if not validation["passed"]:
        print(f"\n  mismatches ({len(validation['mismatches'])}):")
        print(f"  {'idx':<6} {'inputs':<30} {'expected':>8} {'computed':>8}")
        print("  " + "-" * 56)
        for m in validation["mismatches"]:
            input_str = "  ".join(f"{var}={m['inputs'][j]}" for j, var in enumerate(table.variables))
            print(f"  {m['index']:<6} {input_str:<30} {m['expected']:>8} {m['computed']:>8}")
