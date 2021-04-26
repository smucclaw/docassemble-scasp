# This is a parser for the s(CASP) programming language based on pyparsing
# To use, import this file and call program.ParseString(code,True)
# The second parameter is optional, if set to True it will throw an error
# if it is unable to parse any portion of the string provided in code.

# This could be in a stand-alone python package for scasp, but we are only
# using it in the docassemble context, so for now it can be in the docassemble-scasp
# module.

import pyparsing as pp
from pyparsing import *
import string

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
comment = pp.Suppress(COMMENT) + pp.restOfLine('comment')
term = pp.Group(pp.Group(atom)('functor') + pp.Optional(argument_list))('term')
naf_term = pp.Group(NAF + term)('negation as failure')
statement = naf_term | term | constraint

argument <<= statement ^ variable

nlg_dec = pp.Group(pp.Suppress(PRED_DECLARATION) + statement('statement') + pp.Suppress(NLG_ASSIGNMENT) + pp.sglQuotedString('nlg format') + pp.Suppress(PERIOD))('nlg declaration')
rule = pp.Group(pp.Group(statement)('conclusion') + pp.Suppress(IMPLICATION) + pp.Group(pp.delimitedList(pp.OneOrMore(pp.Group(statement))).ignore(comment))('conditions') + pp.Suppress(PERIOD))('rule')
fact = pp.Group(statement + pp.Suppress(PERIOD))('fact')
query = pp.Suppress(QUERY_OP) + pp.Group(pp.delimitedList(pp.Group(statement)))('query') + pp.Suppress(PERIOD)
abducible = pp.Suppress(ABDUC_OP) + statement + pp.Suppress(PERIOD)
import_statement = pp.Suppress(IMPORT_OP) + pp.sglQuotedString('import') + pp.Suppress(PERIOD)
expression = pp.Group(nlg_dec ^ fact ^ rule ^ query ^ abducible ^ import_statement ^ comment)('expression')
program = pp.Group(pp.ZeroOrMore(pp.Group(expression)))('program')
