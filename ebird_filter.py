import pytextfilter as tf

ebird = tf.DelimTxt("ebird", dialect="excel-tab")

# breeding filter
breeding = ebird.create_filter_template(
    "breeding", "BREEDING BIRD ATLAS CODE", str)
breeding.define_operant("!in", lambda x, y: x not in y)
breeding.add_comparison("!in", ["", "F"])

# species
species = ebird.create_filter_template(
    "species", "SCIENTIFIC NAME", str)
species.add_comparison("in")

# date
date = ebird.create_filter_template(
    "date", "OBSERVATION DATE", str)
date.add_comparison(">=")
date.add_comparison("<=")
