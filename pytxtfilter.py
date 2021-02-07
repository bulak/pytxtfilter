"""Module docs
"""


__title__ = 'pytxtfilter'
__version__ = '0.0.2'
__author__ = 'Bulak Arpat'
__license__ = 'GPLv3'
__copyright__ = 'copyright 2020-2021 by Bulak Arpat'


import sys
import operator
import copy
import itertools
import collections
import csv


def quote(var):
    if isinstance(var, int):
        return str(var)
    else:
        return f"'{var}'"


class TxtFilterError(Exception):
    """ docs here
    """
    def __init__(self, msg):
        self.message = msg
        super().__init__(self.message)


class BasicFilter(object):
    """ docs here
    """
    def __init__(self, val_type, comp_func, comp_val, reverse=False):
        self.val_type = val_type
        self.comp_func = comp_func
        self.comp_val = comp_val
        self.reverse_ops = reverse
        self.evaluate = self._get_comp_func()

    def _get_comp_func(self):
        def _fnc(val):
            if self.reverse_ops:
                return self.comp_func(self.comp_val, self.val_type(val))
            else:
                return self.comp_func(self.val_type(val), self.comp_val)
        return _fnc


class Filter(object):
    """ docs here
    """
    operants = {
        "<": (operator.lt, 0),
        "<=": (operator.le, 0),
        "==": (operator.eq, 0),
        "!=": (operator.ne, 0),
        ">=": (operator.ge, 0),
        ">": (operator.gt, 0),
        "in": (operator.contains, 1)
    }

    def __init__(self, name, val_type):
        self.name = name
        self.val_type = val_type
        self.ops = []
        self.comp_vals = []
        self.filters = []

    def define_operant(self, op, comp_func, reverse=False):
        self.operants[op] = (comp_func, reverse)

    def add_comparison(self, op, comp_val = None):
        self.ops.append(op)
        self.comp_vals.append(comp_val)

    def create_comparisons(self, *comp_vals):
        avail_pos = [i for i, val in enumerate(self.comp_vals) if val is None]
        if not len(comp_vals) == len(avail_pos):
            raise TxtFilterError(
                "Number of comparison values do not match required value")
        for i, j in enumerate(avail_pos):
            self.comp_vals[j] = comp_vals[i]
        self.filters = []
        for i, op in enumerate(self.ops):
            try:
                comp_func, reverse = self.operants[op]
            except KeyError:
                print(f"Undefined comparison operant: {op}")
                sys.exit(1)
            except ValueError:
                print(f"Maldefined comparison: {op} => {self.operants[op]}")
                sys.exit(1)
            basic_filter = BasicFilter(self.val_type, comp_func,
                                       self.comp_vals[i], reverse)
            self.filters.append(basic_filter.evaluate)

    def evaluate(self, val):
        return all(f(val) for f in self.filters)
        
    def __str__(self):
        comp_strs = []
        for i, op in enumerate(self.ops):
            comp_str = ["*", op]
            comp_val = self.comp_vals[i]
            if comp_val is not None:
                comp_str.append(str(comp_val))
            else:
                comp_str.append("undef")
            comp_strs.append(f"[{i + 1}]: {' '.join(comp_str)}")
        if not comp_strs:
            comp_strs.append("No comparisons defined")
        comp_strs = "\n".join(comp_strs)
        return f"Filter '{self.name}':\n{comp_strs}"

class ColumnFilter(Filter):
    """ docs here
    """
    def __init__(self, name, column, val_type):
        super().__init__(name, val_type)
        self.column_i = None
        self.apparent_col = column
    def __str__(self):
        f_str = super().__str__()
        return f"{f_str}\nOn column: {quote(self.apparent_col)}"

class DelimTxt(object):
    """Class doc
    """
    def __init__(self, name, has_header=False, dialect=None, encoding=None,
                 **fmtparams):
        self.name = name
        self.has_header = has_header
        self.headers = None
        self.dialect = dialect
        self.encoding = encoding
        self.fmtparams = fmtparams
        self.filters = collections.OrderedDict()
        self.filter_templates = {}

    def _openfile(self, filename):
        try:
            self.filehandle = open(filename, newline="", encoding=self.encoding)
        except IOError as err:
            print(f"Can't open file '{filename}': {err}", file=sys.stderr)
            sys.exit(1)
        self.reader = csv.reader(
            self.filehandle, dialect=self.dialect, **self.fmtparams)
        if self.has_header:
            self.headers = next(self.reader)
        self._update_col_refs()

    def _update_col_refs(self):
        for filtre in self.filters.values():
            if isinstance(filtre.apparent_col, int):
                filtre.column_i = filtre.apparent_col - 1
            else:
                try:
                    col_i = self.headers.index(filtre.apparent_col)
                except ValueError:
                    print(f"Can't find column header name: {filtre.apparent_col}",
                          file=sys.stderr)
                    sys.exit(1)
                else:
                    filtre.column_i = col_i

    def create_filter_template(self, name, column, val_type):
        if not self.has_header and not isinstance(column, int):
            raise TxtFilterError(
                "Column has to be an integer if header is not present")
        column_filter = ColumnFilter(name, column, val_type)
        self.filter_templates[name] = column_filter
        return column_filter

    def print_filter(self, name):
        print(self.filters[name])

    def use_filter(self, name, *comp_vals):
        column_filter = copy.deepcopy(self.filter_templates[name])
        column_filter.create_comparisons(*comp_vals)
        self.filters[name] = column_filter

    def print_filters(self, what=None):
        print_used = not what or what in ["used", "all"]
        print_avail = what in ["avail", "available", "all"]
        if not any([print_used, print_avail]):
            raise TxtFilterError("print_filters arg what can be one of 'used', "
                                 "'avail', 'available' or 'all'")
        if print_used:
            print("== Filters in use ==")
            for i, f in enumerate(self.filters.values()):
                print(f"{i + 1}. {f}\n")
        if print_avail:
            i = 0
            title = "== Available filters =="
            if print_used:
                title = "== Unused available filters =="
            print(title)
            for n, f in self.filter_templates.items():
                in_use = ""
                if print_used and n in self.filters:
                    continue
                if not print_used and n in self.filters:
                    in_use = "  *in use*"
                i += 1
                print(f"{i}. {f}{in_use}\n")

    def process(self, filename):
        self._openfile(filename)
        evals = [(f.column_i, f.evaluate) for f in self.filters.values()]
        writer = csv.writer(sys.stdout, dialect=self.dialect, **self.fmtparams)
        if self.has_header:
            writer.writerow(self.headers)
        count = 0
        for row in self.reader:
            count += 1
            passed = all(func(row[column]) for column, func in evals)
            if passed:
                writer.writerow(row)

if __name__ == "__main__":
    delimtxt = DelimTxt("ebird", has_header=True, dialect="excel-tab")
    breeding = delimtxt.create_filter_template(
        "breeding", "BREEDING BIRD ATLAS CODE", str)
    breeding.define_operant("!in", lambda x, y: x not in y)
    breeding.add_comparison("!in", ["", "F"])
    species = delimtxt.create_filter_template(
        "species", 6, str)
    species.add_comparison("==")
    delimtxt.use_filter("breeding")
    delimtxt.use_filter("species", "Periparus ater")
#    print(species)
#    delimtxt.print_filter("breeding")
#    delimtxt.print_filters()
    delimtxt.process(sys.argv[1])
