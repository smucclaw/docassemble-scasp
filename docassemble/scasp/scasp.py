import pyparsing as pp
from pyparsing import *
import string
import tempfile
import subprocess

__all__ = ['parse', 'Reasoner', 'Response', 'Query']

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

base_atom = pp.Word(string.ascii_lowercase + LOGICAL_NEGATION, pp.printables, excludeChars="(),#.:%")("base atom")
neg_atom = pp.Group(LOGICAL_NEGATION + base_atom)("negative atom")
atom = base_atom | neg_atom
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
# TODO: There are things being reported as positive predicates that are really parameters.
# I need to distinguish between the two.

def parse(code):
    return program.parseString(code,True)

class Reasoner():
    def __init__(self,code,scasp_location='scasp'):
        self.scasp_location = scasp_location
        self.code = code
        self.parse = parse(code)

    def ask(self,question="",number=0):
        number_flag = "-s" + str(number)
        file = tempfile.NamedTemporaryFile(mode='w', suffix='pl',delete=False)
        file.write(self.code + '\n?- ' + question + '.\n')
        file.close()

        output = subprocess.run([self.scasp_location, '--human', '--tree', number_flag, file.name], capture_output=True).stdout.decode('utf-8')

        return Response(output)

    def get_relevant(self,question):
        print("Starting relevance search for " + question)
        search = SearchObject(self.code,question)
        self.get_relevant_inner(question,search)
        return search.relevant

    def get_relevant_inner(self,question,search,expected=1):
        #Generate Code
        code = ""
        #Take The Existing Code Base
        code = self.code
        # Remove Rules That Derive Mapped Predicates
        # Add Abudicibility Statements for Mapped Predicates
        for m in search.mapped:
            code += self.make_abducible(m)
        # Add Abducibility Statements for Input Predicates
        for i in search.inputs:
            code += self.make_abducible(i)
        # Send the query, get the results
        response = Reasoner(code).ask(question)
        result = response.output
        if 'answers' in result:
            number_of_answers = len(result['answers'])
        else:
            number_of_answers = 0
        # If you get n results, analyze result n.
        if number_of_answers == expected:
            current_answer = result['answers'][expected-1]
            # Get the list of all unmapped derived predicates.
            simplified_model = [self.simplify_model_statement(p) for p in current_answer['model']]
            derived_predicates_in_model = [x for x in simplified_model if x in search.derived]
            unmapped_derived_predicates_in_model = [x for x in derived_predicates_in_model if x not in search.mapped and x != question and x not in search.deferred]
            # If there are unmapped derived predicate, run this function once against each of them.
            for new_predicate in unmapped_derived_predicates_in_model:
                search.deferred.add(question)
                self.get_relevant_inner(new_predicate,search)
                search.deferred.remove(question)
                print("  - Marking " + new_predicate + " as mapped.")
                search.mapped.add(new_predicate)
            # Once? this predicate doesn't have any more unmapped predicates?
            # Add all of the input predicates present to the relevance list.
            for i in [x for x in simplified_model if x in search.inputs and x not in search.relevant]:
                print("  - Adding " + i + " as relevant.")
                search.relevant.add(i)
            # Increase n by 1 and start again.
            self.get_relevant_inner(question,search,expected+1)
        # If you get n-1 results:
        elif number_of_answers == expected-1:
            return
        else:
            raise Exception("Got an unexpected number of answers.")
    
    def simplify_model_statement(self, model_statement):
        model_statement = model_statement.replace('not ','').replace('-','') #Remove negations
        constraint = re.compile(r"\| \{[^\}]*\}") # Remove constraints
        model_predicate = constraint.sub('',model_statement)
        return self.generalize_statement(model_predicate)

    def generalize_statement(self,statement):
        statement_parts = re.compile(r"[^\s(),]*(\(.*)\)?")
        matches = statement_parts.match(statement)
        if matches:
            if matches.group(1): #The predicate has parameters
                parameters = re.compile(r"[^\s(),]+(?:\([^\)]+\))?")
                param_matches = parameters.findall(matches.group(1))
                for pm in param_matches:
                    statement = statement.replace(pm,pm.replace(',','_').replace('(','_').replace(')',"_"))
                    
        statement_parts = re.compile(r"([^\(]*)(?:\(([^\)]*)\))?")
        matches = statement_parts.match(statement)
        if matches.group(2):
            parameters = matches.group(2).split(',')
        else:
            parameters = []
        return matches.group(1) + "/" + str(len(parameters))
    
    def make_abducible(self,predicate):
        return "#abducible " + self.expand_predicate(predicate) + ".\n"

    def expand_predicate(self,predicate):
        predicate_parts = re.compile(r"([^\/]*)\/(.*)")
        match = predicate_parts.match(predicate)
        output = match.group(1)
        number = int(match.group(2))
        if number > 0:
            output += "(" + ','.join(string.ascii_uppercase[0:number]) + ")"
        return output
    
    def generalize_scasp_argument(self,argument):
        if 'variable' in argument:
            output = argument['variable']
        if 'term' in argument:
            output = argument['term']['functor']['base atom']
            if 'arguments' in argument['term']:
                output += "("
                for a in argument['term']['arguments']:
                    output += self.generalize_scasp_argument(a)
                    output += ","
                output += ")"
        return output.replace(",)",")")

    def generalize_scasp_variables(self,argument):
        var_index = 0
        var_dict = {}
        # Count variables in the reformatted statement
        variable_pattern = re.compile(r"([A-Z][^\(\)\<\%\,]*)")
        matches = variable_pattern.findall(argument)
        # Go through the variables
        for i in range(len(matches)):
            if matches[i] in var_dict:
                replacement = var_dict[matches[i]]
            else:
                replacement = string.ascii_uppercase[var_index]
                var_dict[matches[i]] = replacement
                var_index = var_index + 1
        output = argument
        for k,v in var_dict.items():
            output = output.replace(k,v)
        return output

    def generalize(self,argument):
        return self.generalize_scasp_variables(self.generalize_scasp_argument(argument))

class SearchObject():
    # This class is used internally to track information about an ongoing
    # relevance search.
    # Code is the original source code, and question is the root query.
    def __init__(self,code,question):
        self.mapped = set()
        self.relevant = set()
        self.base_code = code
        self.query = "\n?- " + question + ".\n"
        self.parse = program.parseString(code,True)
        self.predicates = self.get_predicates()
        self.derived = self.get_derived()
        self.inputs = self.get_inputs()
        self.deferred = set()
        
    def get_predicates(self):
        return set(self.entity_search(self.parse,'base atom'))

    def get_inputs(self):
        return set([x for x in self.predicates if x not in self.derived])
    
    def get_derived(self):
        rules = self.entity_search(self.parse,'rule')
        conclusions = []
        derived = []
        for r in rules:
            conclusions += self.entity_search(r,'conclusion')
        for c in conclusions:
            derived += self.entity_search(c,'positive predicate')
        return set(derived)

    def entity_search(self,l,target):
        results = []
        if target in l:
            results.append(l[target] + "/" + str(len(l['statement']['parameters'])))
        for i in range(len(l)):
            if target in l[i-1]:
                results.append(l[i-1][target] + "/" + str(len(l[i-1]['statement']['parameters'])))
            if isinstance(l[i-1],ParseResults):
                child_search = self.entity_search(l[i-1],target)
                if len(child_search):
                    results += child_search
        return results
    
    def get_arity(self,statement):
        return len(statement['parameter list'])

class Response():
    def __init__(self,input):
        # Put code to build data structure from the input here.
        self.raw = input
        self.output = {}
        # If result is no models
        if input.endswith('no models\n\n'):
            query = input.replace('\n\nno models\n\n','').replace('\n    ','').replace('QUERY:','')
            self.output['query'] = query
            self.output['result'] = 'No'
            return
        else:
            # Divide up the remainder into individual answers
            answers = input.split("\tANSWER:\t")
            query = answers[0]
            del answers[0]
            query = query.replace('\n','').replace('     ',' ').replace('QUERY:','')
            self.output['query'] = query
            self.output['result'] = 'Yes'
            self.output['answers'] = []
            
            # for each actual answer
            for a in answers:
                #Separate out the time, tree, model, and bindings
                answer_parts = a.split('\n\nJUSTIFICATION_TREE:\n')
                time = answer_parts[0]
                answer_parts = answer_parts[1].split('\n\nMODEL:\n')
                tree = answer_parts[0]
                answer_parts = answer_parts[1].split('\n\nBINDINGS:')
                model = answer_parts[0]
                bindings = []
                # The bindings may not exist
                if len(answer_parts) > 1:
                    bindings = answer_parts[1].splitlines()
                # Reformat the Time
                time = time.replace(' ms)','').replace('(in ','').split(' ')[1]

                # Reformat the Tree Into Nested Dictionary, or something like that.
                explanations = self.make_tree(self.get_depths(tree.splitlines()))

                # Reformat the Model
                model = model.replace('{ ','').replace(' }','').split(',  ')

                # Reformat the Bindings
                if bindings:
                    bindings = [b for b in bindings if b != '' and b != ' ']
                    bindings = [b.replace(' equal ',': ') for b in bindings]

                # Create a dictionary for this answer
                new_answer = {}
                new_answer['time'] = time
                new_answer['model'] = model
                if bindings:
                    new_answer['bindings'] = bindings
                new_answer['explanations'] = explanations

                # Add the answer to the output_answers list
                self.output['answers'].append(new_answer.copy())
    
    def make_tree(self,depth_lines,depth=0):
        output = []
        skip = 0
        for i in range(len(depth_lines)):
            if skip > 0:
                skip = skip-1
                continue
            # If the depth has gone shallower, go back.
            if depth_lines[i]['depth'] < depth:
                break
            # If the next line is the same depth (this line has no children) return only this line.
            elif len(depth_lines)-1 > i and depth_lines[i]['depth'] == depth_lines[i+1]['depth']:
                output.append({'text': depth_lines[i]['text']})
            # Otherwise (this line has children), return this line's text, and make a tree of its children.
            else:
                children = self.make_tree(depth_lines[i+1:],depth_lines[i]['depth']+1)
                skip = len(children)
                output.append({'text': depth_lines[i]['text'], 'children': children})
        return output

    def get_depths(self,lines):
        output = []
        for l in lines:
            this_line = {}
            depth = (len(l) - len(l.lstrip(' ')))/4
            this_line['text'] = l.lstrip(' ')
            this_line['depth'] = depth
            output.append(this_line.copy())
        return output

#mortal = open('docassemble/scasp/data/static/r34.pl','r')
#code = mortal.read()
#mortal.close()
#test_reasoner = Reasoner(code)
#print(test_reasoner.parse.dump())

#response = test_reasoner.ask('mortal(X)')
#print(response.output['answers'][0]['explanations'])
#relevant = test_reasoner.get_relevant('mortal(X)')


