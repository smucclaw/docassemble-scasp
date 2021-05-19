# This is a basic parser designed to be able to parse the components of a
# response from sCASP to a query.

# To use it, take the text returned by the scasp reasoner and provide it
# to responseparser.response.parseString(response,True). The second parameter
# indicates whether the parser should expect to be able to parse the entire
# input, and throw an error if that is not the case.

# This is designed to deal with the output of a query using the --tree flag,
# the -s0 flag, but not the --human flag.

import pyparsing as pp
from pyparsing import *
import string

LPAREN,RPAREN,LBRACKET,RBRACKET,SEP,PERIOD,EQ_OP,LOGICAL_NEGATION = map(pp.Literal,"(){},.=-")
IMPLICATION = ":-"
QUERY_OP = "?-"
DISEQ_OP = "\="
NAF = "not"

base_atom = pp.Word(string.ascii_lowercase + LOGICAL_NEGATION, pp.printables, excludeChars="(),#.:%")("base atom")
neg_atom = pp.Combine(pp.Suppress(LOGICAL_NEGATION) + base_atom)("negative atom")
atom = neg_atom | base_atom
named_var = pp.Word(string.ascii_uppercase, pp.printables, excludeChars="(),#.:%")("variable")
silent_var = pp.Literal("_")('silent variable')
variable = named_var | silent_var
symbol = atom ^ variable
argument = pp.Forward()
argument_list = pp.Suppress(LPAREN) + pp.delimitedList(pp.OneOrMore(pp.Group(argument)))('arguments') + pp.Suppress(RPAREN)
constraint_op = pp.Literal(DISEQ_OP)('disequality') | pp.Literal(EQ_OP)('equality')
constraint = pp.Group(pp.Group(symbol)('leftside') + constraint_op('operator') + pp.Group(symbol)('rightside'))('constraint')
term = pp.Group(pp.Group(atom)('functor') + pp.Optional(argument_list))('term')
naf_term = pp.Group(NAF + term)('negation as failure')
statement = naf_term | term | constraint

argument <<= statement ^ variable



# A response is a query followed by the response content.

# A query is the query prompt followed by a query.
query = pp.Suppress(QUERY_OP) + pp.Group(pp.delimitedList(pp.Group(statement)))('query') + pp.Suppress(PERIOD)

# Response content is either no models, or a set of answers.

# No models is just the text "no models" alone on a line.

# An answer is an answer number, and optional justification tree, a model, and a bindings set.

# An answer number is ANSWER: followed by a number, followed by a runtime.

# A runtime is (in X ms) where X is a float

# A model is the word MODEL: Followed by {, an optional list of model entries, and }.

# Bindings set is the word BINDINGS: followed optionally by a list of bindings.

# A binding is a variable name, an equal sign, and a value on a line.

# A justification tree is a list of justifications

# A justification is either a fact or a conclusion.

# A fact is a statement, followed by a period.
fact = pp.Group(statement + pp.Suppress(PERIOD))('fact')

# A conclusion is a statement followed by an implication, followed by one or more justifications.


