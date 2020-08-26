import pytextfilter as tf

ebird = tf.DelimTxt("ebird", has_header=True, dialect="excel-tab")

# breeding filter
breeding = ebird.create_filter_template(
    "breeding", "BREEDING BIRD ATLAS CODE", str)
breeding.define_operant("!in", lambda x, y: x not in y)
breeding.add_comparison("!in", ["", "F"])

# species
species = ebird.create_filter_template(
    "species", 6, str)
species.add_comparison("in")

# date
date = ebird.create_filter_template(
    "date", 28, str)
date.add_comparison(">=")
date.add_comparison("<=")
