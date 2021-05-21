# This is a basic parser designed to be able to parse the components of a
# response from sCASP to a query.

# To use it, take the text returned by the scasp reasoner and pre-process
# it using the annotate_indents(string) function, and then provide the result
# to response.parseString(string,True). The second parameter
# indicates whether the parser should expect to be able to parse the entire
# input, and throw an error if that doesn't happen.

# An example of loading a file and displaying the resulting parse tree is:
#
# responsefile = open('filename.txt', 'r')
# responsetext = responsefile.read()
# print(yaml.dump(response.parseString(responsetext,True).asDict()))

# YAML is the easiest way to visualize the resulting parse trees.
# pyparsing's internal display methods contain too much redudant information
# to be legible for large trees.

# This parser is designed to deal with the output of a query using the --tree flag,
# the -s0 flag, but NOT the --human flag.

# It uses a grammar that is similar to, but not identical to
# the grammar defined in the scaspparser.py file. Even where they share
# components, some of the components in this parser have been improved.
# Those improvements will be back-ported to scaspparser.py at a later date.

import pyparsing as pp
from pyparsing import *
import string
import yaml


TESTING = True
DISPLAY_UNEXPECTED_TEST_RESULTS_ONLY = True

if TESTING:
    pp.enable_all_warnings()


test_count = 0
pass_count = 0
fail_count = 0

def test(description,object,string,should_parse=True):
    global test_count
    global pass_count
    global fail_count
    test_count = test_count + 1
    try:
        parse = object.parseString(string,True).asDict()
    except ParseException as err:
        parsed = False
        message = err
    else:
        parsed = True
    finally:
        if parsed == should_parse:
            pass_count += 1
        else:
            fail_count += 1
        if parsed != should_parse or not DISPLAY_UNEXPECTED_TEST_RESULTS_ONLY:
            print("-----\nTest:\t" + description)
            print("Using:\t" + string)
            print("Result:\n")
            if parsed:
                print(yaml.dump(parse))
            else:
                print(message)
    
def annotate_indents(code):

    UPINDENT = "{{UP}}"
    DOWNINDENT = "{{DOWN}}"

    # First, turn the code into a list of tuples, for the code and the number of prepended spaces
    # This shouldn't be required if we take tokens from the parser?
    lines = code.splitlines()
    annotated_lines = []
    for l in lines:
        if not l.lstrip().startswith("ANSWER:"):
            spaces = len(l) - len(l.lstrip(' '))
        else:
            spaces = 0
        annotated_lines.append((l,spaces))

    # Second, check to see if there are any broken indentations
    levels = []
    new_strings = []
    for (text,l) in annotated_lines:
        if levels == []:
            # This is the first line, add its level.
            levels.append(l)
            new_strings.append(text)
        elif l == levels[-1]:
            # This line is the same level, just add it.
            new_strings.append(text)
        elif l > levels[-1]:
            # The indentation level has increased
            new_strings.append(UPINDENT)
            new_strings.append(text)
            levels.append(l)
        elif l < levels[-1]:
            if l in levels:
                while l != levels[-1]:
                    new_strings.append(DOWNINDENT)
                    levels.pop()
                new_strings.append(text)
            else:
                # The indentation has gone down, but to
                # a level of indentation not currently in
                # the stack. Throw an error.
                raise Exception("Unexpected indentation level.")
    
    return "\n".join(new_strings)



LPAREN,RPAREN,LBRACKET,RBRACKET,SEP,PERIOD,LOGICAL_NEGATION,CONSTR = map(pp.Literal,"(){},.-|")
IMPLICATION = ":-"
QUERY_OP = "?-"
DISEQ_OP = "\="
EQ_OP = "="
NAF = "not"
UPINDENT = "{{UP}}"
DOWNINDENT = "{{DOWN}}"

base_atom = pp.Word(string.ascii_lowercase+pp.nums, pp.printables, excludeChars="(),#.:%{}}=\\")("base atom")
neg_atom = pp.Combine(LOGICAL_NEGATION + base_atom)("negative atom")
atom = neg_atom | base_atom
named_var = pp.Word(string.ascii_uppercase, pp.printables, excludeChars="(),#.:%{}=\\")("variable")
silent_var = pp.Literal("_")('silent variable')
variable = pp.Forward()
symbol = atom ^ variable
argument = pp.Forward()
argument_list = pp.Suppress(LPAREN) + pp.delimitedList(pp.Group(argument))('arguments') + pp.Suppress(RPAREN)
constraint_op = pp.Literal(DISEQ_OP)('disequality') | pp.Literal(EQ_OP)('equality')
constraint = Group(symbol)('left side') + Group(constraint_op)('operator') + Group(symbol)('right side')
term = pp.Group(pp.Group(atom)('functor') + pp.Optional(argument_list))('term')
naf_term = pp.Group(NAF + term)('negation as failure')
statement = naf_term | term | constraint
query = pp.Suppress(QUERY_OP) + pp.Group(pp.delimitedList(pp.Group(statement)))('query') + pp.Suppress(PERIOD)
argument <<= statement ^ variable

# A query is the query prompt followed by a query.
query_statement = pp.Literal("QUERY:") + query

# No models is just the text "no models" alone on a line.
no_models = pp.Literal("no models")('no models')

# A runtime is (in X ms) where X is a float
runtime = pp.Literal("(in") + pp.Word(pp.nums+'.')('time') + pp.Literal("ms)")

# A Unity is a Variable an equal sign, and a value
unity = pp.Group(pp.Group(variable)('variable') + pp.Suppress(EQ_OP) + pp.Group(symbol)('binding'))('unity')
    
# A disunity is a Variable, a not equal sign, and a value
disunity = pp.Group(pp.Group(variable)('variable') + pp.Suppress(DISEQ_OP) + pp.Group(symbol)('binding'))('disunity')

# A variable constraint is a constraint indicator, and a bracketed comma delimited list of disunities
variable_constraint = CONSTR + LBRACKET + pp.Group(pp.delimitedList(pp.Group(disunity)))('constraints') + RBRACKET

# A variable is either a named variable or a silent variable, with an optional
# variable constraint
variable <<= (named_var | silent_var) + pp.Optional(variable_constraint)

# A binding is a variable name, an equal sign, and a value on a line.
binding = unity | disunity

# Bindings set is the word BINDINGS: followed optionally by a list of bindings.
bindings_set = pp.Literal("BINDINGS:") + pp.ZeroOrMore(pp.Group(pp.delimitedList(pp.Group(binding))))('bindings')

# A model is the word MODEL: Followed by {, an optional list of model entries, and }.
model = pp.Literal("MODEL:") + LBRACKET + pp.delimitedList(pp.ZeroOrMore(pp.Group(statement)))('model') + RBRACKET

reason = pp.Forward()

list_of_reasons = pp.OneOrMore(pp.Group(reason) \
                    + pp.Optional(pp.Suppress(SEP)))('list of reasons')\
                    + pp.Optional(pp.Suppress(PERIOD))
# TODO: Add Tests

# A conclusion is a statement, an implication symbol, and an indented list of reasons.
conclusion = pp.Group(pp.Group(statement)('implication conclusion') + pp.Suppress(IMPLICATION) + UPINDENT + list_of_reasons + DOWNINDENT)

# A reason is either a conclusion, or a statement.
reason <<= pp.Group(conclusion)('implication reason') ^ pp.Group(term)('term reason')

# A justification tree is JUSTIFICATION_TREE: followed by a list of reasons.
justification = pp.Suppress(pp.Literal("JUSTIFICATION_TREE:")) + list_of_reasons

# An answer is an answer number, and optional justification tree, a model, and a bindings set.
answer = pp.Suppress(pp.Literal("ANSWER:")) + pp.Word(pp.nums)('answer number') + runtime + pp.Optional(justification)('justification') + model + bindings_set

# Response content is either no models, or a set of answers.
response_content = no_models | pp.ZeroOrMore(pp.Group(answer))('answer set')

# A response is a query followed by the response content.
response = query_statement + response_content

# A fact is a statement, followed by a period.
fact = pp.Group(statement + pp.Suppress(PERIOD))('fact')

# A conclusion is a statement followed by an implication, followed by one or more justifications.

if TESTING:
    print("     --- Testing Argument ---")
    test("Good argument - var",argument,"A")
    test("Good argument - term",argument,"test(A)")
    test("Good argument - atom",argument,"test")

    print("     --- Testing Argument List ---")
    test("Good argument list",argument_list,"(A,test,C)")
    test("Good arg list with terms",argument_list,"(A,test(B),C,test)")
    test("No opening parens",argument_list,"A,B)",False)
    test("No closing parens",argument_list,"(A,B",False)
    test("No separators",argument_list,"(A B C)",False) #TODO Incorrectly Succeeds.

    print("     --- Testing Term ---")
    test("Good term",term,"test(A)")
    test("Good term nullary",term,"test")
    test("Good term binary",term,"test(A,B)")
    test("Bad term, capitalized functor",term,"Test(A)",False)
    test("Good nested term",term,"test(one(A),B)")

    print("     --- Testing NAF Term ---")
    test("Good NAF term",naf_term,"not test(A)")
    test("Bad NAF, missing NAF",naf_term,"test",False)
    test("Good NAF term nullary",naf_term,"not test")
    test("Good NAF term binary",naf_term,"not test(A,B)")
    test("Bad NAF term, capitalized functor",naf_term,"not Test(A)",False)
    test("Good NAF nested term",naf_term,"not test(one(A),B)")

    print("     --- Testing Conclusion ---")
    test("Good Conclusion",conclusion,"winner_of_game(P | {P \= 1},G) :- {{UP}} test. {{DOWN}}") # TODO: Not Working

    print("     --- Testing Model ---")
    test("Good model",model,"MODEL:\n{ winner_of_game(P | {P \= 1,P \= 2},G),  player(P | {P \= 1}),  player(1),  game(G),  player_in_game(P | {P \= 1},G),  player_in_game(1,G),  player_threw_sign(P | {P \= 1},rock),  player_threw_sign(1,scissors),  sign_beats_sign(rock,scissors) }")
    # TODO: Add More Tests

    print("     --- Testing Bindings Set ---")
    test("Good empty bindings set",bindings_set,"""\
        BINDINGS:
        """)
    test("Good bindings set",bindings_set,"""\
        BINDINGS:
        Awesome = you
        """)
    test("Good multiple bindings per variable",bindings_set,"""\
        BINDINGS:
        P \= a,P \= b
        Awesome = you
        """)

    print("     --- Testing Binding ---")
    test("Good binding disunity",binding,"A\=test")
    test("Good binding disunity",binding,"A \= A")
    test("Missing Operator",binding,"A test",False)
    test("Missing Operand",binding,"A \= ",False)
    test("Good binding unity",binding,"A\=test")
    test("Good binding unity",binding,"A \= A")
    test("Missing Operator",binding,"A test",False)
    test("Missing Operand",binding,"A \= ",False)
    
    print("     --- Testing Variable ---")
    test("Good named variable",variable,"Test")
    test("Good silent variable",variable,"_")
    test("Bad variable",variable,"test",False)

    print("     --- Testing Variable Constraint ---")
    test("Good variable constraint",variable_constraint,"| {P \= 1}")
    test("Missing bar",variable_constraint," {P = A}",False)
    test("Missing bracket",variable_constraint,"| {P=1",False)
    test("Not valid binding",variable_constraint,"| { P - 2 }",False)
    test("Mutliple Constraints",variable_constraint,"| {P \= 1,P \= 2}")

    print("     --- Testing Disunity ---")
    test("Good disunity",disunity,"A\=test")
    test("Good disunity",disunity,"A \= A")
    test("Missing Operator",disunity,"A test",False)
    test("Wrong Operator",disunity,"A = B",False)
    test("Missing Operand",disunity,"A \= ",False)

    print("     --- Testing Unity ---")
    test("Good unity",unity,"A=test")
    test("Good unity",unity,"A = A")
    test("Missing Operator",unity,"A test",False)
    test("Wrong Operator",unity,"A \= B",False)
    test("Missing Operand",unity,"A = ",False)

    print("     --- Testing Runtime ---")
    test("Good timing",runtime,"(in 0.003ms)")
    test("Weird numbers",runtime,"(in 0.1.3.ms)")

    print("     --- Testing No Model ---")
    test("No models",no_models,"      no models   ")
    test("Bad no models",no_models,"anything else",False)

    print("     --- Testing Query Statement ---")
    test("Good query statement",query_statement,"QUERY:?- mortal(socrates).")
    # TODO Add tests

    print("     --- Testing Constraint ---")
    test("Good constraint",constraint,"A=B")
    test("Good Inequality Constraint",constraint,"A\=test")
    test("No left side",constraint,"=A",False)
    test("No Right Side",constraint,"A=",False)
    test("No Operator",constraint,"A B",False)

    print("     --- Testing Base Atom ---")
    test("Good Atom",base_atom,"atom_34")
    test("Base Atom not Capitalized",base_atom,"A34",False)
    test("Numbers OK",base_atom,"123werg")
    test("No Excluded Chars",base_atom,"test(this",False)

    print("     --- Testing Logically Negated Base Atom ---")
    test("Negated Atom",neg_atom,"-test")
    test("Not Negated",neg_atom,"test",False)

    print("     --- Testing Atom ---")
    test("Good atom",atom,"test")
    test("Good Negated",atom,"-test")
    test("Bad atom (capital)",atom,"Test",False)

    print("     --- Testing Named Variable ---")
    test("Good named var",named_var,"Test")
    test("Bad named var",named_var,"test",False)
    test("not allowed char",named_var,"Te%st",False)

    print("     --- Testing Silent Variable ---")
    test("Good silent",silent_var,"_")
    test("Bad silent",silent_var,"A",False)

    print("     --- Testing Symbol ---")
    test("Good symbol atom",symbol,"test")
    test("Good symbol variable",symbol,"Test")
    test("Badd symbol, bad atom",symbol,"test()",False)

    print("     --- Testing Constraint Operator ---")
    test("Equality is constraint op",constraint_op,"=")
    test("Disequality is constraint op",constraint_op,"\=")
    test("Nothign else is constriant op",constraint_op,"test",False)

    print("     --- Testing Statement ---")
    # TODO: Add tests

    print("     --- Testing Query ---")
    # TODO: Add tests

    print("     --- Testing Justification Tree ---")
    test("Good Justification Tree",justification,"""\
        JUSTIFICATION_TREE:
winner_of_game(P | {P \= 1},G) :-
{{UP}}
    player(P | {P \= 1}) :-
{{UP}}
        chs(player(P | {P \= 1})),
        abducible(player(P | {P \= 1})) :-
{{UP}}
            abducible(player(P | {P \= 1})).
{{DOWN}}
{{DOWN}}
{{DOWN}}
global_constraints.""")


    print("     --- Testing Answer ---")
    

    test("Answer",answer,"""\
                ANSWER: 1 (in 7.265 ms)

JUSTIFICATION_TREE:
winner_of_game(1,testgame) :-
{{UP}}
    player(1),
    player(2),
    game(testgame),
    player_in_game(1,testgame) :-
    {{UP}}
        chs(player_in_game(1,testgame)),
        abducible(player_in_game(1,testgame)) :-
        {{UP}}
            abducible(player_in_game(1,testgame)).
            {{DOWN}}
            {{DOWN}}
    player_in_game(2,testgame) :-
    {{UP}}
        chs(player_in_game(2,testgame)),
        abducible(player_in_game(2,testgame)) :-
        {{UP}}
            abducible(player_in_game(2,testgame)).
            {{DOWN}}
            {{DOWN}}
    player_threw_sign(1,rock) :-
    {{UP}}
        chs(player_threw_sign(1,rock)),
        abducible(player_threw_sign(1,rock)) :-
        {{UP}}
            abducible(player_threw_sign(1,rock)).
            {{DOWN}}
            {{DOWN}}
    player_threw_sign(2,scissors) :-
    {{UP}}
        chs(player_threw_sign(2,scissors)),
        abducible(player_threw_sign(2,scissors)) :-
        {{UP}}
            abducible(player_threw_sign(2,scissors)).
            {{DOWN}}
            {{DOWN}}
    sign_beats_sign(rock,scissors).
    {{DOWN}}
global_constraint.

MODEL:
{ winner_of_game(1,testgame),  player(1),  player(2),  game(testgame),  player_in_game(1,testgame),  player_in_game(2,testgame),  player_threw_sign(1,rock),  player_threw_sign(2,scissors),  sign_beats_sign(rock,scissors) }

BINDINGS: 
Player = 1 
Game = testgame""")


    print("          --- Testing Response ---")

    file = 'example_no_model.txt'
    responsefile = open('docassemble/scasp/data/static/' + file, 'r')
    code = responsefile.read()
    test("No Model Response",response,annotate_indents(code))

    file = 'example_no_bindings.txt'
    responsefile = open('docassemble/scasp/data/static/' + file, 'r')
    code = responsefile.read()
    test("Response with no Bindings",response,annotate_indents(code))
    
    file = 'example_model.txt'
    responsefile = open('docassemble/scasp/data/static/' + file, 'r')
    code = responsefile.read()
    test("Response with Bindings",response,annotate_indents(code))
    
    file = 'example_disunity.txt'
    responsefile = open('docassemble/scasp/data/static/' + file, 'r')
    code = responsefile.read()
    test("Response With Disunity Constraints",response,annotate_indents(code))


    print("Tests Run: " + str(test_count))
    print("Passed: " + str(pass_count))
    print("Failed: " + str(fail_count))
    print("Percentage: " + str(int((pass_count/test_count)*100)) + "%")


