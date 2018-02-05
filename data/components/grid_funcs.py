
def find_repeats(iterable, min_length, excludes=None):
    excludes = [None] if excludes is None else excludes
    matches = []
    potential = None
    for i, x in enumerate(iterable):
        if potential is None:
            if x not in excludes:
                potential = [(i, x)]
        else:
            if potential[-1][1] == x:
                potential.append((i, x))
            else:
                if len(potential) >= min_length:
                    matches.append((p[0] for p in potential))
                potential = [(i, x)]
    if potential and len(potential) >= min_length:
        matches.append((p[0] for p in potential))
    return matches

def find_row_matches(nested_list, min_length, excludes=None):
    matches = []
    for j, row in enumerate(nested_list):
        row_indexes = find_repeats(row, min_length, excludes)
        for repeats in row_indexes:
            matches.append([(x, j) for x in repeats])
    return matches

def find_column_matches(nested_list, min_length, excludes=None):
    matches = []
    num_columns = len(nested_list[0])
    for i in range(num_columns):
        column = [row[i] for row in nested_list]
        column_indexes = find_repeats(column, min_length, excludes)
        for repeats in column_indexes:
            matches.append([(i, y) for y in repeats])
    return matches

def find_grid_matches(nested_list, min_length, excludes=None):
    matches = find_row_matches(nested_list, min_length, excludes)
    matches.extend(find_column_matches(nested_list, min_length, excludes))
    return matches
