import sys
import operator
import itertools
import csv


class BasicFilter(object):

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
#        self.ops.append(self.operants[op])
        self.ops.append(op)
#        comp_strs = ["*", op, "undef"]
#        if comp_val is not None:
        self.comp_vals.append(comp_val)
#            comp_strs[-1] = str(comp_val)
#        if self.operants[op][1]:
#            comp_strs.reverse()
#        self.
    def create_comparisons(self, *comp_vals):
        if comp_vals:
            assert len(comp_vals) == len(self.ops)
            self.comp_vals = comp_vals
        assert len(self.ops) == len(self.comp_vals)
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
            comp_strs.append(f"[{i}]: {' '.join(comp_str)}")
        if not comp_strs:
            comp_strs.append("No comparisons defined")
        comp_strs = "\n".join(comp_strs)
        return f"Filter '{self.name}':\n{comp_strs}"

class ColumnFilter(Filter):
    def __init__(self, name, column, val_type):
        super().__init__(name, val_type)
        self.column = column


class DelimTxt(object):
    """
    Class doc
    """
    def __init__(self, name, has_header=False, dialect=None, **fmtparams):
        self.name = name
        self.has_header = has_header
        self.headers = None
        self.dialect = dialect
        self.fmtparams = fmtparams
        self.filters = []
        self.filter_templates = {}

    def _openfile(self, filename):
        try:
            self.filehandle = open(filename, newline="")
        except IOError as err:
            print(f"Can't open file '{filename}': {err}", file=sys.stderr)
            sys.exit(1)
        self.reader = csv.reader(
            self.filehandle, dialect=self.dialect, **self.fmtparams)
        if self.has_header:
            self.headers = next(self.reader)
        self._update_col_refs()

    def _update_col_refs(self):
        for filtre in self.filters:
            if not isinstance(filtre.column, int):
                try:
                    col_i = self.headers.index(filtre.column)
                except ValueError:
                    print(f"Can't find column header name: {filtre.column}",
                          file=sys.stderr)
                    sys.exit(1)
                else:
                    filtre.column = col_i
            else:
                # Column numbers start with 1
                filtre.column -= 1

    def create_filter_template(self, name, column, val_type):
        column_filter = ColumnFilter(name, column, val_type)
        self.filter_templates[name] = column_filter
        return column_filter

    def use_filter(self, name, *comp_vals):
        column_filter = self.filter_templates[name]
        column_filter.create_comparisons(*comp_vals)
        self.filters.append(column_filter)

    def print_filters(self):
        for f in self.filters:
            print(f"{f.name} at {f.column}")

    def process(self, filename):
        self._openfile(filename)
        writer = csv.writer(sys.stdout, dialect=self.dialect)
        if self.has_header:
            writer.writerow(self.headers)
        for row in self.reader:
            passed = all(f.evaluate(row[f.column]) for f in self.filters)
            if passed:
                writer.writerow(row)

if __name__ == "__main__":
    delimtxt = DelimTxt("ebird", dialect="excel-tab")
    breeding = delimtxt.create_filter_template(
        "breeding", "BREEDING BIRD ATLAS CODE", str)
    breeding.define_operant("!in", lambda x, y: x not in y)
    breeding.add_comparison("!in", ["", "F"])
    species = delimtxt.create_filter_template(
        "species", 5, str)
        #"SCIENTIFIC NAME", str)
    species.add_comparison("==")
    delimtxt.use_filter("breeding")
    delimtxt.use_filter("species", "Periparus ater")
    delimtxt.process(sys.argv[1])
