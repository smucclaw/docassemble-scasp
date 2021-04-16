import pyparsing as pp
from pyparsing import *
import string

# This is a tool for parsing s(CASP) code in Python, so that we can do useful things with the code more easily.

LPAREN,RPAREN,SEP,PERIOD,COMMENT = map(pp.Literal,"(),.%")
IMPLICATION = ":-"
PRED_DECLARATION = "#pred"
NLG_ASSIGNMENT = "::"
QUERY_OP = "?-"
ABDUC_OP = "#abducible"
IMPORT_OP = "#import"
DISEQ_OP = "\="
EQ_OP = "="
NAF = "not"
LOGICAL_NEGATION = '-'

pos_atom = pp.Word(string.ascii_lowercase + LOGICAL_NEGATION, pp.printables, excludeChars="(),#.:%")("positive atom")
neg_atom = pp.Group(LOGICAL_NEGATION + pp.Word(string.ascii_lowercase, pp.printables, excludeChars="(),#.:%"))("negative atom")
atom = pos_atom | neg_atom
named_var = pp.Word(string.ascii_uppercase, pp.printables, excludeChars="(),#.:%")("variable")
silent_var = pp.Literal("_")('silent variable')
variable = named_var | silent_var
symbol = atom ^ variable
parameter = pp.Forward()
parameter_list = pp.Suppress(LPAREN) + pp.delimitedList(pp.OneOrMore(pp.Group(parameter)))('parameters') + pp.Suppress(RPAREN)
constraint_op = pp.Literal(DISEQ_OP)('disequality') | pp.Literal(EQ_OP)('equality')
constraint = pp.Group(pp.Group(symbol)('leftside') + constraint_op('operator') + pp.Group(symbol)('rightside'))('constraint')
comment = pp.Suppress(COMMENT) + pp.restOfLine('comment')
pos_statement = pos_atom('positive predicate') ^ pp.Group(pos_atom('_ positive predicate') + parameter_list)('statement')
neg_statement = neg_atom('negative predicate') ^ pp.Group(neg_atom('_ negative predicate') + parameter_list)('statement')
base_statement = neg_statement | pos_statement
naf_statement = pp.Group(NAF + base_statement)('negation as failure')
statement = naf_statement | base_statement | constraint
parameter <<= statement ^ variable
nlg_dec = pp.Group(pp.Suppress(PRED_DECLARATION) + statement('statement') + pp.Suppress(NLG_ASSIGNMENT) + pp.sglQuotedString('nlg format') + pp.Suppress(PERIOD))('nlg declaration')
rule = pp.Group(pp.Group(statement)('conclusion') + pp.Suppress(IMPLICATION) + pp.Group(pp.delimitedList(pp.OneOrMore(pp.Group(statement))).ignore(comment))('conditions') + pp.Suppress(PERIOD))('rule')
fact = statement('fact') + pp.Suppress(PERIOD)
query = pp.Suppress(QUERY_OP) + pp.Group(pp.delimitedList(pp.Group(statement)))('query') + pp.Suppress(PERIOD)
abducible = pp.Suppress(ABDUC_OP) + statement + pp.Suppress(PERIOD)
import_statement = pp.Suppress(IMPORT_OP) + pp.sglQuotedString('import') + pp.Suppress(PERIOD)
expression = pp.Group(nlg_dec ^ fact ^ rule ^ query ^ abducible ^ import_statement ^ comment)('expression')
program = pp.Group(pp.ZeroOrMore(pp.Group(expression)))('program')

#tests
# print(atom.parseString('this_is_an_atom',True).dump())
# print(variable.parseString("Variable",True).dump())
# print(variable.parseString("_",True).dump())
# print(symbol.parseString('atom',True).dump())
# print(symbol.parseString('Var',True).dump())
# print(symbol.parseString('_',True).dump())
# print(parameter_list.parseString('(A,b,r345)',True).dump())
# print(statement.parseString('according_to(Rule,must_not(jason,accept,ceo_MegaCorp))', True).dump())
# print(statement.parseString('-according_to(Rule,must_not(jason,accept,ceo_MegaCorp))', True).dump())
# print(naf_statement.parseString('not according_to(Rule,must_not(jason,accept,ceo_MegaCorp))', True).dump())
# print(statement.parseString('not according_to(Rule,must_not(jason,accept,ceo_MegaCorp))', True).dump())
# print(statement.parseString('nullary_predicate',True).dump())
# print(nlg_dec.parseString("#pred test(X,Y) :: '@(X) is a test of @(Y)'.", True).dump())
# print(rule.parseString("mortal(X) :- human(X).", True).dump())
# print(fact.parseString("human(socrates).",True).dump())
# print(query.parseString("?- mortal(X).", True).dump())
# print(comment.parseString("% This is a comment.", True).dump())
# print(abducible.parseString("#abducible awesome(jason).", True).dump()) # TODO: It is calling things "predicate" that are actually just nullary parameters
# print(import_statement.parseString("#import 'filename'.", True).dump())
# print(expression.parseString("?- mortal(X). % I'm curious if this works.", True).dump())

# print(program.parseFile(open('docassemble/scasp/data/static/mortal.pl','r'), True).dump())
# print(program.parseString("#pred this(X) :: '@(X) is a this'.\nthis(jason).\n",True).dump())
#print(constraint.parseString('X \= Y',True).dump())
#print(constraint.parseString('X = practice_of_law',True).dump())
# with open('docassemble/scasp/data/static/r34.pl','r') as inputfile:
#    try:
#        print(program.parseFile(inputfile, True).dump())
#    except pp.ParseException as pe:
#        print(pe.line)
#        print(' '*(pe.col-1) + '^')
#        print(pe)

# TODO: Comments at the end of lines inside rule conditions are getting dropped entirely.
# Not a major issue, really, but we might want to try to do better.
