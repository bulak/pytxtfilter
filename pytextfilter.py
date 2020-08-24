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
        self.ops.append(self.operants[op])
        if comp_val is not None:
            self.comp_vals.append(comp_val)
    def create_comparisons(self, *comp_vals):
        if comp_vals:
            assert len(comp_vals) == len(self.ops)
            self.comp_vals = comp_vals
        self.filters = []
        for i, (comp_func, reverse) in enumerate(self.ops):
            basic_filter = BasicFilter(self.val_type, comp_func,
                                       self.comp_vals[i], reverse)
            self.filters.append(basic_filter.evaluate)
    def evaluate(self, val):
        return all(f(val) for f in self.filters)


class ColumnFilter(Filter):
    def __init__(self, name, column, val_type):
        super().__init__(name, val_type)
        self.column = column


class DelimTxt(object):
    def __init__(self, name, fieldnames=None, restkey=None, restval=None,
                 dialect=None, *args, **kargs):
        self.name = name
        self.fieldnames = fieldnames
        self.restkey = restkey
        self.restval = restval
        self.dialect = dialect
        self.args = args
        self.kargs = kargs
        self.filters = []
        self.filter_templates = {}
    def _openfile(self, filename):
        try:
            self.filehandle = open(filename, newline="")
        except IOError as err:
            print(f"Can't open file '{filename}': {err}", file=sys.stderr)
            sys.exit(1)
        self.reader = csv.DictReader(
            self.filehandle, fieldnames=self.fieldnames, restkey=self.restkey,
            restval=self.restval, dialect=self.dialect, *self.args, **self.kargs)
    def create_filter_template(self, name, column, val_type):
        column_filter = ColumnFilter(name, column, val_type)
        self.filter_templates[name] = column_filter
        return column_filter
    def use_filter(self, name, *comp_vals):
        column_filter = self.filter_templates[name]
        column_filter.create_comparisons(*comp_vals)
        self.filters.append(column_filter)
    def process(self, filename):
        self._openfile(filename)
        writer = csv.DictWriter(sys.stdout, fieldnames=self.reader.fieldnames,
                                dialect=self.dialect)
        writer.writeheader()
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
        "species", "SCIENTIFIC NAME", str)
    species.add_comparison("==")
    delimtxt.use_filter("breeding")
    delimtxt.use_filter("species", "Periparus ater")
    delimtxt.process(sys.argv[1])
