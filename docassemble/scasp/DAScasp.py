# A simple interface to the s(CASP) constraint answer set programming
# tool from inside a Docassemble interview.

import string
import os
import subprocess
import urllib.parse
import re
import sys
import docassemble.scasp.scasp as scasp
try:
    from docassemble.base.functions import get_config
    from docassemble.base.core import DAFile, DAObject
except ModuleNotFoundError:
    not_docassemble_context = True



# OK, we need to organize this out better.
# We have a number of things going on:
# 1. Send information to the reasoner, and collect the results.
# 2. Reformat those results for displaying to the user.
# 3. Get Data about an s(CASP) file
# 4. Generate an interview.
# 5. Figure out what is relevant to a query. That is done to generate an interview.

# So typically, you would have a reasoner object, which would have a query method,
# and which would return an answer object.

# Reasoner
#   - send query, get results.
#   - configure it?
# Answer
#   - just holds information about itself in a predictable structure.
#   - maybe function for displaying it inside Docassemble, inside the major

# Docassemble-scasp
#   Depends on:
#       scasp-reasoner
#           Provides:
#               - Ability to send queries to s(CASP) reasoner and receive Python
#                 structured results
#   Provides:
#     - Ability to translate docassemble interview data into s(CASP) encodings (and back?).
#     - Ability to display scasp responses in Docassemble pages.
#     - Ability to configure the reasoner from inside the docassemble configuration files.

class Response():
    # A class which receives the text provided by an s(CASP) reasoner response,
    # and creates self.raw and self.output from it.
    # self.output is a dictionary with 'query' and 'result', and optionally 'answers' if there are any.
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
                explanations = get_depths(tree.splitlines())

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

# Takes a list of lines from an explanation and returns a list of nested dictionaries of text and children dictionaries.
def get_depths(lines):
    output = []
    for l in lines:
        # If we get to global constraints, stop.
        if l.startswith('The global constraints hold'):
            break
        # Skip lines that start with 'abducible' holds
        if l.lstrip(' ').startswith('\'abducible\' holds'):
            continue
        this_line = {}
        depth = (len(l) - len(l.lstrip(' ')))/4
        this_line['text'] = l.lstrip(' ')
        # s(CASP) applies periods to some lines that we don't display, so
        # just get rid of them all.
        if this_line['text'].endswith('.'):
            this_line['text'] = this_line['text'].rstrip('.')
        this_line['depth'] = depth
        output.append(this_line.copy())
    return output



# Docassemble-L4
#   Depends On:
#       - docassemble-scasp
#       - docassemble-datatypes
#       - LExSIS
#       - scasp-parse
#           Provides:
#               - Ability to get information about scasp files
#   Provides:
#       - Ability to generate an interview from an s(CASP) file and a LExSIS file.
#       - Ability to run that interview using the l4-specific parts, such as excluding
#         certain defeasibility predicates used in L4 from explanations, etc.

# FOR TESTING ONLY
#import yaml
#data_structure_file = open('r34.yml',"r")
#data_structure = yaml.load(data_structure_file,Loader=yaml.FullLoader)
#query = "?- legally_holds(Rule,must_not(Lawyer,accept,Position))."
#rules_file = open('r34.pl',"r")
#rules = rules_file.read()
#rules = "#pred mortal(X) :: '@(X) is mortal'.\n#pred human(X) :: '@(X) is human'.\n#pred other(X) :: '@(X) is other'.\nmortal(X) :- human(X).\nmortal(X) :- other(X)."


# Send an s(CASP) file to the reasoner and return the results.
def sendQuery(filename, number=0):
    number_flag = "-s" + str(number)
    #scasp_location = get_config('scasp')['location'] if (get_config('scasp') and get_config('scasp')['location']) else '/var/www/.ciao/build/bin/scasp'
    scasp_location = 'scasp'
    results = subprocess.run([scasp_location, '--human', '--tree', number_flag, filename], capture_output=True).stdout.decode('utf-8')
    
    pattern = re.compile(r"daSCASP_([^),\s]*)")
    matches = list(pattern.finditer(results))
    for m in matches:
        results = results.replace(m.group(0),urllib.parse.unquote_plus(m.group(1).replace('__perc__','%').replace('__plus__','+')))
    
    output = {}

    # If result is no models
    if results.endswith('no models\n\n'):
        query = results.replace('\n\nno models\n\n','').replace('\n    ','').replace('QUERY:','')
        output['query'] = query
        output['result'] = 'No'
        return output
    else:
        # Divide up the remainder into individual answers
        answers = results.split("\tANSWER:\t")
        query = answers[0]
        del answers[0]
        query = query.replace('\n','').replace('     ',' ').replace('QUERY:','')
        output['query'] = query
        output['result'] = 'Yes'
        output['answers'] = []
        
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

            # Reformat the Tree
            explanations = make_tree(tree)
            explanations = display_list(explanations)

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
            output['answers'].append(new_answer.copy())
        
        # Now add the output answers to the result
        return output

def get_depths(lines):
    output = []
    for l in lines:
        # If we get to global constraints, stop.
        if l.startswith('The global constraints hold'):
            break
        # Skip lines that start with 'abducible' holds
        if l.lstrip(' ').startswith('\'abducible\' holds'):
            continue
        this_line = {}
        depth = (len(l) - len(l.lstrip(' ')))/4
        this_line['text'] = l.lstrip(' ')
        # s(CASP) applies periods to some lines that we don't display, so
        # just get rid of them all.
        if this_line['text'].endswith('.'):
            this_line['text'] = this_line['text'].rstrip('.')
        this_line['depth'] = depth
        output.append(this_line.copy())
    return output

def make_tree(lines):
    # Add depth information to the lines
    lines = lines.splitlines()
    meta_lines = get_depths(lines)

    return meta_lines

def display_list(input,depth=0):
    if depth==0:
        output = "<ul id=\"explanation\" class=\"active\">"
    else:
        output = "<ul class=\"nested\">"
    skip = 0
    for i in range(len(input)):
        if skip > 0:
            skip = skip-1
            continue
        while input[i]['depth'] < depth:
            output += "</li></ul>"
            depth = depth-1
        if input[i]['depth'] == depth:
            if input[i]['text'].endswith('because'):
                output += "<li><span class=\"caret\">"
            else:
                output += "<li>"
            output += input[i]['text']
            if input[i]['text'].endswith('because'):
                output += "</span>"
            else:
                output += "</li>"
        if input[i]['depth'] > depth:
            sub_output = display_list(input[i:],input[i]['depth'])
            skip = sub_output.count("<li>") # skip the parts already done.
            output += sub_output

    output += "</ul>"
    return output

exclusions = [
    'rule/1',
    'conclusion/1',
    'conclusion/3', # Should be removed later.
    'legally_holds/2',
    'according_to/2',
    'according_to/4', # should be removed later.
    'overrides/4',
    'opposes/4',
    'rebutted_by/4',
    'refuted_by/4',
    'compromised/2',
    'defeated_by_closure/4',
    'disqualified/2',
    'defeated/2',
    'defeated_by_rebuttal/4',
    'defeated_by_refutation/4',
    'defeated_by_disqualification/4',
    'opposes2/4',
    'unsafe_rebutted_by/4'
]

def get_predicates(input):
    predicates = set()
    predicate = re.compile(r"^\#pred ([^-][^\s]*) :: ", re.M)
    for p in predicate.finditer(input):
        if generalize_predicate(p.group(1)) not in exclusions:
            predicates.add(generalize_predicate(p.group(1)))
    return list(predicates)

def get_rule_conclusions(input):
    conclusions = set()
    rule = re.compile(r"^([^\s]*) \:\-", re.M)
    for r in rule.finditer(input):
        if generalize_predicate(r.group(1)) not in exclusions:
            conclusions.add(generalize_predicate(r.group(1)))
    return conclusions

def get_inputs(input):
    predicates = get_predicates(input)
    conclusions = get_rule_conclusions(input)
    inputs = []
    for p in predicates:
        if p not in conclusions:
            inputs.append(p)
    return inputs

def make_abducible(predicates):
    output = ""
    for p in predicates:
        output += "#abducible " + expand_predicate(p) + ".\n"
    return output

# TODO: Stop it from using both kinds of negation.
# TODO: It is mis-counting the number of elements in predicates that have functions
# as parameters. Remove the unnecessary exclusions when that is fixed.

def get_relevant(rules,query,facts=""):
    # Find all the input predicates
    inputs = get_inputs(rules)
    # Create a temporary file
    code = DAFile()
    code.initialize(filename="tempcode",extension="pl")
    #code = open('tempcode.pl','x')
    # Add the rules to the temporary file
    content = rules + "\n"
    #code.write(rules + "\n")
    # Add the abducibility statements to the temporary file
    content += make_abducible(inputs)
    #code.write(make_abducible(inputs))
    # Add the query to the temporary file.
    content += "?- " + query
    #code.write(query.replace('legally_holds','according_to'))
    # Save the file
    code.write(content)
    #code.close()
    # Run the code
    results = sendQuery(code.path(),10) #just to see
    #results = sendQuery('tempcode.pl',10)
    # Take the union of all of the predicates in all of the answers
    # that are not conclusions
    relevant = set()
    conclusions = get_rule_conclusions(rules)
    for a in results['answers']:
        for p in a['model']:
            if generalize_predicate(p) not in conclusions and \
               generalize_predicate(p) not in exclusions and \
               not generalize_predicate(p).startswith('not') and \
               not generalize_predicate(p).startswith('-'):
                relevant.add(generalize_predicate(p))
    # Later we will need to filter by more stuff.
    return relevant

def build_agenda(relevant,data_structure):
    # Using a list of relevant predicates, create an agenda of questions
    # to ask in the given interview.
    agenda = list()
    for r in relevant:
        for d in data_structure['data']:
            target = find_element_for_encoding(d,expand_predicate(r))
            if target:
                agenda.append(add_index(target))
    return agenda

def expand_predicate(predicate):
    predicate_parts = re.compile(r"([^\/]*)\/(.*)")
    match = predicate_parts.match(predicate)
    output = match.group(1)
    number = int(match.group(2))
    if number > 0:
        output += "(" + ','.join(string.ascii_uppercase[0:number]) + ")"
    return output


def generalize_predicate(predicate):
    predicate_parts = re.compile(r"[^\s(),]*(\(.*)\)?")
    matches = predicate_parts.match(predicate)
    if matches:
        if matches.group(1): #The predicate has parameters
            parameters = re.compile(r"[^\s(),]+(?:\([^\)]+\))?")
            param_matches = parameters.findall(matches.group(1))
            for pm in param_matches:
                predicate = predicate.replace(pm,pm.replace(',','_').replace('(','_').replace(')',"_"))
                
    predicate_parts = re.compile(r"([^\(]*)(?:\(([^\)]*)\))?")
    matches = predicate_parts.match(predicate)
    if matches.group(2):
        parameters = matches.group(2).split(',')
    else:
        parameters = []
    return matches.group(1) + "/" + str(len(parameters))

def find_element_for_encoding(data_element,encoding):
    if 'encodings' in data_element:
        for e in data_element['encodings']:
            if expand_predicate(generalize_predicate(e)) == encoding:
                if is_list(data_element):
                    return data_element['name'] + '.gather()'
                else:
                    return data_element['name'] + '.value'
    if 'attributes' in data_element:
        for a in data_element['attributes']:
            value = find_element_for_encoding(a,encoding)
            if value:
                if is_list(data_element):
                    return data_element['name'] + "[LIST]." + value
                else:
                    return data_element['name'] + "." + value

def add_index(agenda_item):
    # Take a string and replace each instance of [LIST] with [i] through [m]
    if agenda_item.count('LIST') > 5:
        raise Exception('Docassemble cannot handle nested lists of depth > 5')
    else:
        return agenda_item.replace('LIST','i',1).replace('LIST','j',1).replace('LIST','k',1).replace('LIST','l',1).replace('LIST','m',1)

def is_list(input):
    # Something with exactly 1 or 0 values is not a list.
    if 'exactly' in input and (input['exactly'] == 1 or input['exactly'] == 0):
        return False
    # Something with a minimum of more than one, or with a minumum and no maximum
    # is a list
    if 'minimum' in input:
        if input['minimum'] > 1:
            return True
        if 'maximum' not in input:
            return True
    # Something with a maximum above one is a list
    if 'maximum' in input and input['maximum'] > 1:
        return True
    # Something with an exact number above 1 is a list
    if 'exactly' in input and input['exactly'] > 1:
        return True
    # Something that is optional should be treated as though it was a list
    # in that you should ask whether it exists before collecting it, but only
    # collect the one.
    if 'minimum' in input and 'maximum' in input:
        if input['minimum'] == 0 and input['maximum'] == 1:
            return True
    # Otherwise
    return False

def generate_agendas(rules,query,data_structure):
    rel = get_relevant(rules,query)
    subagenda = []
    for r in rel:
        for d in data_structure['data']:
            target = find_element_for_encoding(d,expand_predicate(r))
            if target:
                subagenda.append(add_index(target))
    agenda = set()
    for s in subagenda:
        agenda.add(find_root(s))
    return (list(agenda), subagenda)

def find_root(s):
    pattern = re.compile(r"([^\[]*)\[[ijklm]\].*")
    match = pattern.match(s)
    if match:
        return match.group(1) + ".gather()"
    else:
        return s


# Script to generate a Docassemble Interview using
# DADataType object types and the s(CASP) reasoner on the basis of a YAML
# description of a data structure.


from os import error
import yaml

def generate_interview(sourcefile):
    data_structure = yaml.load(sourcefile, Loader=yaml.FullLoader)
    
    ## Include Docassemble-l4, which imports docassemble.scasp and docassemble.datatypes
    output = "include:\n"
    output += "  - docassemble.l4:l4.yml\n"
    output += "---\n"

    ## Not sure why, but this seems to be necessary.
    output += "modules:\n"
    output += "  - docassemble.datatypes.DADataType\n"
    output += "---\n"

    ## Generate the parameters for DAScasp
    output += "mandatory: True \n"
    output += "code: |\n"
    output += "  ruleSource = user_info().package + \":" + data_structure['rules'] + "\"\n"
    output += "  query = \"" + data_structure['query'] + ".\"\n"
    if 'options' in data_structure:
        if 'show models' in data_structure['options']:
            output += "  show_models = " + str(data_structure['options']['show models']) + "\n"
        if 'answers' in data_structure['options']:
            if data_structure['options']['answers'] == "all":
                output += "  scasp_number = 0" + "\n"
            else:
                output += "  scasp_number = " + str(data_structure['options']['answers']) + "\n"
    output += "---\n"

    ## Copy the terms from the source file
    if 'terms' in data_structure:
        output += "terms:\n"
        output += yaml.dump(data_structure['terms'],width=1000000)
        output += "---\n"

    ## Include the Source File So It Can Be Accessed At RunTime
    output += "variable name: data_structure\n"
    output += "data:\n  "
    output += '  '.join(yaml.dump(data_structure,width=1000000).splitlines(True))
    output += "---\n"


    ## Generate Objects Block
    output += "objects:\n"
    for var in data_structure['data']:
        output += generate_object(var)
    output += "---\n"

    ## Generate Code Blocks for Lists.
    for var in data_structure['data']:
        output += make_complete_code_block(var)

    ## Generate Agenda Block (Temporarily Including Everything in The Root)
    #output += "variable name: agenda\n"
    #output += "data:\n"
    #for var in data_structure['data']:
    #    output += add_to_agenda(var)
    #output += "---\n"

    ## Generate a Code Block That will Generate s(CASP) code.
    output += "code: |\n"
    output += "  import urllib\n"
    output += "  facts = \"\"\n"
    for var in data_structure['data']:
        output += generate_translation_code(var)
    output += "---\n"

    ## Generate a Code Block that defines the .parent_value
    ## and .self_value attribute for all objects.
    for var in data_structure['data']:
        output += generate_parent_values(var)

    ## Generate Code For Agenda and Sub-Agenda
    output += "code: |\n"
    output += "  (agenda, subagenda) = generate_agendas(rules.slurp(),query,data_structure)\n"
    output += "---\n"

    ## Generate Mandatory Code Block That Will Prompt Collection
    output += "mandatory: True\n"
    output += "code: |\n"
    output += "  for a in agenda:\n"
    output += "    exec(a)\n"
    output += "---\n"

    ## Generate The Closing Question
    output += "mandatory: True\n"
    output += "question: Finished\n"
    output += "subquestion: |\n"
    output += "  ${ DAScasp_show_answers }\n"
    output += "---\n"

    ## Print the output (for testing)
    return output

def add_to_agenda(input_object,root=""):
    #For the main element
    # If it is a list, add it to the agenda with a .gather()
    # Otherwise, add it to the list with a .value
    # For Each Attribute
    # Add the attribute to the list.
    output = ""
    if root == "":
        dot = ""
    else:
        dot = "."
    if "[i]" not in root:
        level = "[i]"
    else:
        if "[j]" not in root:
            level = "[j]"
        else:
            if "[k]" not in root:
                level = "[k]"
            else:
                if "[l]" not in root:
                    level = "[l]"
                else:
                    if "[m]" not in root:
                        level = "[m]"
                    else:
                        raise error("Docassemble cannot handle nested lists of depth > 5")
    if is_list(input_object):
        new_root = root + dot + input_object['name'] + level
        this_root = root + dot + input_object['name']
    else:
        new_root = root + dot + input_object['name']
        this_root = new_root
    if is_list(input_object):
       output += "  - " + this_root + ".gather()\n"
    else:
       output += "  - " + this_root + ".value\n"
    return output

def generate_parent_values(input_object,parent="",parent_is_list=False,parent_is_objref=False):
    output = ""
    if "[i]" not in parent:
        nextlevel = "[i]"
        level=""
    else:
        if "[j]" not in parent:
            nextlevel = "[j]"
            level = "[i]"
        else:
            if "[k]" not in parent:
                nextlevel = "[k]"
                level = "[j]"
            else:
                if "[l]" not in parent:
                    nextlevel = "[l]"
                    level = "[k]"
                else:
                    if "[m]" not in parent:
                        nextlevel = "[m]"
                        level = "[l]"
                    else:
                        raise error("Docassemble cannot handle nested lists of depth > 5")
    if parent == "":
        dot = ""
    else:
        dot = "."
    if parent_is_list:
        index = nextlevel
    else:
        index = level
    output += "code: |\n"
    output += "  " + parent + index + dot + input_object['name'] + '.self_value = "' + input_object['name'].replace('_',' ') + '"\n'
    if parent != "": # This object has a parent
        output += "  " + parent + index + dot + input_object['name'] + ".parent_value = " + parent + index + (".value.value" if parent_is_objref else ".value") + "\n"
    else:
        output += "  " + parent + index + dot + input_object['name'] + ".parent_value = ''\n"
    if is_list(input_object):
        if 'any' in input_object:
            output += "  " + parent + index + dot + input_object['name'] + ".any = \"" + input_object['any'].replace('{Y}',"\" + " + parent + index + dot + input_object['name'] + ".parent_value + \"") + "\"\n"
        else:
            output += "  " + parent + index + dot + input_object['name'] + ".any = \"\"\n"
        if 'another' in input_object:
            output += "  " + parent + index + dot + input_object['name'] + ".another = \"" + input_object['another'].replace('{Y}',"\" + " + parent + index + dot + input_object['name'] + ".parent_value + \"") + "\"\n"
        else:
            output += "  " + parent + index + dot + input_object['name'] + ".another = \"\"\n"
    else:
        if 'ask' in input_object:
            output += "  " + parent + index + dot + input_object['name'] + ".ask = \"" + input_object['ask'].replace('{Y}',"\" + " + parent + index + ".tell + \"") + "\"\n"
        else:
            output += "  " + parent + index + dot + input_object['name'] + ".ask = \"\"\n"
        if 'tell' in input_object:
            output += "---\ncode: |\n"
            output += "  " + parent + index + dot + input_object['name'] + ".tell = \"" + input_object['tell'].replace('{X}',"\" + " + parent + index + dot + input_object['name'] + (".value.value" if input_object['type'] == 'Object' else ".value") + " + \"").replace('{Y}',"\" + " + parent + index + ".tell + \"") + "\"\n"
        else:
            output += "---\ncode: |\n"
            output += "  " + parent + index + dot + input_object['name'] + ".tell = " + parent + index + dot + input_object['name'] + (".value.value" if parent_is_objref else ".value") + "\n"    
    output += "---\n"
    if is_list(input_object):
        if index == "[i]": nextindex = "[j]"
        if index == "[j]": nextindex = "[k]"
        if index == "[k]": nextindex = "[l]"
        if index == "[l]": nextindex = "[m]"
        if index == "": nextindex = "[i]"
        output += "code: |\n"
        output += "  " + parent + index + dot + input_object['name'] + nextindex + '.self_value = "' + input_object['name'].replace('_',' ') + '"\n'
        if parent != "": # This object has a parent
            output += "  " + parent + index + dot + input_object['name'] + nextindex + ".parent_value = " + parent + index + (".value.value" if parent_is_objref else ".value") + '\n'
        else:
            output += "  " + parent + index + dot + input_object['name'] + nextindex + ".parent_value = ''\n"
        if 'ask' in input_object:
            output += "  " + parent + index + dot + input_object['name'] + nextindex + ".ask = \"" + input_object['ask'].replace('{Y}',"\" + " + parent + index + ".tell + \"") + "\"\n"
        else:
            output += "  " + parent + index + dot + input_object['name'] + nextindex + ".ask = \"\"\n"
        if 'tell' in input_object:
            output += "---\ncode: |\n"
            output += "  " + parent + index + dot + input_object['name'] + nextindex + ".tell = \"" + input_object['tell'].replace('{X}',"\" + " + parent + index + dot + input_object['name'] + nextindex + (".value.value" if input_object['type'] == 'Object' else ".value") + " + \"").replace('{Y}',"\" + " + parent + index + ".tell + \"") + "\"\n"
        else:
            output += "---\ncode: |\n"
            output += "  " + parent + index + dot + input_object['name'] + nextindex + ".tell = " + parent + index + dot + input_object['name'] + nextindex + (".value.value" if input_object['type'] == 'Object' else ".value") + "\n"  
        output += "---\n"
    if 'attributes' in input_object:
        for a in input_object['attributes']:
            output += generate_parent_values(a,parent + index + dot + input_object['name'],is_list(input_object),input_object['type'] == 'Object')
    return output

def generate_translation_code(input_object,indent_level=2,parent=""):
    # TODO: Object References should return .value.value
    output = ""
    def indent(): return (" ") * indent_level
    # output += indent() + "# Regarding " + input_object['name'] + "\n"
    if is_list(input_object):
        if parent == "": # This is a root list
            output += indent() + "if defined('" + input_object['name'] + "'):\n"
            output += indent() + "  for " + input_object['name'] + "_element in " + input_object['name'] + ":\n"
        else: # This is a non-root list
            output += indent() + "if defined('" + parent + "." + input_object['name'] + "'):\n"
            output += indent() + "  for " + input_object['name'] + "_element in " + parent + "." + input_object['name'] + ":\n"
        indent_level += 4
        if 'encodings' in input_object:
            if input_object['type'] == "Boolean":
                if parent == "":
                    output += indent() + "if defined('" + input_object['name'] + "_element.value') and " + input_object['name'] + "_element.value:\n"
                else:
                    output += indent() + "if defined('" + parent + "." + input_object['name'] + "_element.value') and " + parent + "." + input_object['name'] + "_element.value:\n"
            else:
                if parent == "":
                    output += indent() + "if defined('" + input_object['name'] + "_element.value'):\n"
                else:
                    output += indent() + "if defined('" + parent + "." + input_object['name'] + "_element.value'):\n"
            indent_level += 2
            for e in input_object['encodings']:
                if parent == "":
                    output += indent() + "facts += \"" + e.replace('X',"daSCASP_\" + urllib.parse.quote_plus(str(" + input_object['name'] + "_element.value)).replace('%','__perc__').replace('+','__plus__') + \"") + ".\\n\"\n"
                else:
                    output += indent() + "facts += \"" + e.replace('X',"daSCASP_\" + urllib.parse.quote_plus(str(" + input_object['name'] + "_element.value)).replace('%','__perc__').replace('+','__plus__') + \"").replace('Y',"daSCASP_\" + urllib.parse.quote_plus(str(" + parent + ".value)).replace('%','__perc__').replace('+','__plus__') + \"") + ".\\n\"\n"
            # if input_object['type'] == "Boolean": # we are now indenting for everything.
            indent_level -= 2
        if 'attributes' in input_object:
            for a in input_object['attributes']:
                output += generate_translation_code(a,indent_level,input_object['name'] + "_element")
        output += indent() + "pass # to end empty for loops\n"
    else: # This is not a list.
        if 'encodings' in input_object:
            if input_object['type'] == "Boolean":
                if parent == "":
                    output += indent() + "if defined('" + input_object['name'] + ".value') and " + input_object['name'] + ".value:\n"
                else:
                    output += indent() + "if defined('" + parent + "." + input_object['name'] + ".value') and " + parent + "." + input_object['name'] + ".value:\n"
            else:
                if parent == "":
                    output += indent() + "if defined('" + input_object['name'] + ".value'):\n"
                else:
                    output += indent() + "if defined('" + parent + "." + input_object['name'] + ".value'):\n"
            indent_level += 2
            for e in input_object['encodings']:
                if parent == "":
                    output += indent() + "facts += \"" + e.replace('X',"daSCASP_\" + urllib.parse.quote_plus(str(" + input_object['name'] + ".value)).replace('%','__perc__').replace('+','__plus__') + \"") + ".\\n\"\n"
                else:
                    output += indent() + "facts += \"" + e.replace('X',"daSCASP_\" + urllib.parse.quote_plus(str(" + parent + "." + input_object['name'] + ".value)).replace('%','__perc__').replace('+','__plus__') + \"").replace('Y',"daSCASP_\" + urllib.parse.quote_plus(str(" + parent + ".value)).replace('%','__perc__').replace('+','__plus__') + \"") + ".\\n\"\n"
            #if input_object['type'] == "Boolean":
            indent_level -= 2
        if 'attributes' in input_object:
            for a in input_object['attributes']:
                if parent == "":
                    output += generate_translation_code(a,indent_level,input_object['name'])
                else:
                    output += generate_translation_code(a,indent_level,parent + "." + input_object['name'])
    return output

def make_complete_code_block(input_object,root=""):
    output = ""
    if root == "":
        dot = ""
    else:
        dot = "."
    if "[i]" not in root:
        level = "[i]"
    else:
        if "[j]" not in root:
            level = "[j]"
        else:
            if "[k]" not in root:
                level = "[k]"
            else:
                if "[l]" not in root:
                    level = "[l]"
                else:
                    if "[m]" not in root:
                        level = "[m]"
                    else:
                        raise error("Docassemble cannot handle nested lists of depth > 5")
    if is_list(input_object):
        new_root = root + dot + input_object['name'] + level
    else:
        new_root = root + dot + input_object['name']
    if is_list(input_object):
        output += "code: |\n"
        output += "  if \"" + new_root + ".value\" in subagenda:\n"
        output += "    " + new_root + ".value\n"
        if 'attributes' in input_object:
            for a in input_object['attributes']:
                if is_list(a):
                    output += "  if \"" + new_root + "." + a['name'] + ".gather()\" in subagenda:\n"
                    output += "    " + new_root + "." + a['name'] + ".gather()\n"
                else:
                    output += "  if \"" + new_root + "." + a['name'] + ".value\" in subagenda:\n"
                    output += "    " + new_root + "." + a['name'] + ".value\n"
        output += "  " + new_root + ".complete =  True\n"
        output += "---\n"
    if 'attributes' in input_object:
        for a in input_object['attributes']:
            output += make_complete_code_block(a,new_root)
    return output

def generate_object(input_object,root=""):
    if root == "":
        dot = ""
    else:
        dot = "."
    if "[i]" not in root:
        level = "[i]"
    else:
        if "[j]" not in root:
            level = "[j]"
        else:
            if "[k]" not in root:
                level = "[k]"
            else:
                if "[l]" not in root:
                    level = "[l]"
                else:
                    if "[m]" not in root:
                        level = "[m]"
                    else:
                        raise error("Docassemble cannot handle nested lists of depth > 5")
    if is_list(input_object):
        new_root = root + dot + input_object['name'] + level
        this_root = root + dot + input_object['name']
    else:
        new_root = root + dot + input_object['name']
        this_root = new_root
    output = "  - " + this_root + ": |\n      "
    if is_list(input_object):
        output += "DAList.using(object_type=" + generate_DADTDataType(input_object['type'])
        if input_object['type'] == "Enum":
            output += ".using(options=" + input_object['options'] + ")"
        if input_object['type'] == "Object":
            output += ".using(source=" + input_object['source'] + ")"
        if 'minimum' in input_object:
            output += ",minimum=" + str(input_object['minimum'])
        if 'maximum' in input_object:
            output += ",maximum=" + str(input_object['maximum'])
        if 'exactly' in input_object:
            output += ",target_number=" + str(input_object['exactly'])
        if 'exactly' in input_object:
            output += ",ask_number=True"
        # The following treats optional single elements as lists of max length 1.
        if 'minimum' in input_object and 'maximum' in input_object:
            if input_object['minimum'] == 0 and input_object['maximum'] == 1:
                output += ",there_is_another=False"
        output += ",complete_attribute=\"complete\")\n"
    else:
        if input_object['type'] == "Enum":
            output += generate_DADTDataType(input_object['type']) + ".using(options="
            output += str(input_object['options']) + ")\n"
        else:
            if input_object['type'] == "Object":
                output += generate_DADTDataType(input_object['type']) + ".using(source="
                output += input_object['source'] + ")\n"
            else:
                output += generate_DADTDataType(input_object['type']) + "\n"
    
    if 'attributes' in input_object:
        for a in input_object['attributes']:
            output += generate_object(a,new_root)
    return output

dadatatypes = {
        "Boolean": "DADTBoolean",
        "Continue": "DADTContinue",
        "String": "DADTString",
        "Enum": "DADTEnum",
        "Number": "DADTNumber",
        "Date": "DADTDate",
        "DateTime": "DADTDateTime",
        "Time": "DADTTime",
        "YesNoMaybe": "DADTYesNoMaybe",
        "File": "DADTFile",
        "Object": "DADTObjectRef"
    }

def generate_DADTDataType(input_type):
    if input_type not in dadatatypes:
        raise error("Unknown datatpye.")
    return dadatatypes.get(input_type)

def is_list(input):
    # Something with exactly 1 or 0 values is not a list.
    if 'exactly' in input and (input['exactly'] == 1 or input['exactly'] == 0):
        return False
    # Something with a minimum of more than one, or with a minumum and no maximum
    # is a list
    if 'minimum' in input:
        if input['minimum'] > 1:
            return True
        if 'maximum' not in input:
            return True
    # Something with a maximum above one is a list
    if 'maximum' in input and input['maximum'] > 1:
        return True
    # Something with an exact number above 1 is a list
    if 'exactly' in input and input['exactly'] > 1:
        return True
    # Something that is optional should be treated as though it was a list
    # in that you should ask whether it exists before collecting it, but only
    # collect the one.
    if 'minimum' in input and 'maximum' in input:
        if input['minimum'] == 0 and input['maximum'] == 1:
            return True
    # Otherwise
    return False

class RelevanceSearch(object):
    def __init__(self,base_code):
        self.mapped = set()
        self.relevant = set()
        self.base_code = base_code
        self.inputs = []
        self.derived = []
        self.query = ""
        self.ast = []

def get_initially_relevant(query,base_code):
    print('Starting relevance search.\n')
    # The algorithm her requires that it recursively search through the conditions of
    # rules until it finds conditions that are exclusively input predicates, then
    # work it's way back while cutting off the searches it has already finished.
    # So the process should be slow at the start and should speed up as it goes.
    # In order to make that work, the algorithm need to be recursive, but not
    # the list of problems it has already solved. So the inner verson of the function
    # passes an object so that the values of the object can be changed inside the
    # recursive function, and those changes will persist after the function returns.



    mapping_object = map_object()
    # Use the parser to parse the base_code
    mapping_object.ast = scasp.program.parseString(base_code,True)
    mapping_object.mapped = set()
    mapping_object.relevant = set()
    mapping_object.base_code = base_code
    mapping_object.inputs = get_inputs(base_code)
    mapping_object.derived = get_rule_conclusions(base_code)
    mapping_object.query = query
    mapping_object.deferred = set()
    query_predicate = generalize_predicate(query)
    get_initially_relevant_inner(query_predicate,mapping_object)
    return mapping_object.relevant

def simplify_model_predicate(model_predicate):
    model_predicate = model_predicate.replace('not ','').replace('-','')
    constraint = re.compile(r"\| \{[^\}]*\}")
    model_predicate = constraint.sub('',model_predicate)
    return generalize_predicate(model_predicate)

def get_initially_relevant_inner(current,mapping_object,expected=1):
    # Run the target query seeking n results starting at n=1
    # Generate the code
    # Take the existing code base.
    temp_code = ""
    # Remove any statements that derive predicates that are already mapped.
    rule_pattern = re.compile(r"([^\s]*) :-\s+([^\.]*)\.\s*", re.MULTILINE | re.DOTALL) 
    temp_code += mapping_object.base_code
    # print("Removing rules for mapped predicates...\n")
    for r in rule_pattern.finditer(mapping_object.base_code):
        #print("Comparing " + generalize_predicate(r[1]) + " to list of mapped " + str(mapping_object.mapped))
        if generalize_predicate(r[1]) in mapping_object.mapped:
            #print("Removing " + generalize_predicate(r[1]) + ".\n")
            temp_code = temp_code.replace(r[0],'% Removed ' + generalize_predicate(r[1]) + ".\n")
    # Add abducibility statements for the mapped predicates.
    # print("Making mapped predicates abducible...\n" + str(mapping_object.mapped) + "\n")
    temp_code += '\n' + make_abducible(mapping_object.mapped)
    # Add abducibility statements for the input predicates.
    # print("Making input predicates abducible...\n" + str(mapping_object.inputs) + "\n")
    temp_code += '\n' + make_abducible(mapping_object.inputs)
    # Add the query.
    # print("Adding query " + expand_predicate(current) + ".\n")
    temp_code += "?- " + expand_predicate(current) + ".\n"
    #code = DAFile()
    #code.initialize(filename="tempcode",extension="pl")
    #code.write(temp_code)
    #result = sendQuery(code.path(), number=expected)
    code = open('tempfile.pl', "w")
    code.write(temp_code)
    code.close()
    print("Seeking model #" + str(expected) + " for " + current + "...")
    result = sendQuery(code.name, number=expected)
    os.remove(code.name)
    if 'answers' in result:
        #print("Answers received.\n")
        number_of_answers = len(result['answers'])
    else:
        #print("No answers received.\n")
        number_of_answers = 0
    # If you get n results, analyze result n.
    if number_of_answers == expected:
        #print("Expected number of answers received, " + str(expected) + ".\n")
        current_answer = result['answers'][expected-1]
        # Get the list of all unmapped derived predicates.
        #print("The model is " + str(current_answer['model']) + ".\n")
        simplified_model = [simplify_model_predicate(p) for p in current_answer['model']]
        #print("The simplified model is " + str(simplified_model) + ".\n")
        derived_predicates_in_model = [x for x in simplified_model if x in mapping_object.derived]
        #print("The derived predicates present are " + str(derived_predicates_in_model) + ".\n")
        unmapped_derived_predicates_in_model = [x for x in derived_predicates_in_model if x not in mapping_object.mapped and x != current and x not in mapping_object.deferred]
        #print("The unmapped derived, non-query, non-deferred predicates present are " + str(unmapped_derived_predicates_in_model) + ".\n")
        # If there are unmapped derived predicate, run this function once against each of them.
        for new_predicate in unmapped_derived_predicates_in_model:
            #print("Processing " + new_predicate + "...\n")
            mapping_object.deferred.add(current)
            get_initially_relevant_inner(new_predicate,mapping_object)
            mapping_object.deferred.remove(current)
            print("  - Marking " + new_predicate + " as mapped.")
            mapping_object.mapped.add(new_predicate)
        # Once? this predicate doesn't have any more unmapped predicates?
        # Add all of the input predicates present to the relevance list.
        for i in [x for x in simplified_model if x in mapping_object.inputs and x not in mapping_object.relevant]:
            print("  - Adding " + i + " as relevant.")
            mapping_object.relevant.add(i)
        # Increase n by 1 and start again.
        get_initially_relevant_inner(current,mapping_object,expected+1)
    # If you get n-1 results:
    elif number_of_answers == expected-1:
        #print("No more results for this query.\n")
        return
    else:
        raise error("Got an unexpected number of answers.")

rules_file = open('docassemble/scasp/data/static/r34.pl',"r")
rules = rules_file.read()
print(str(get_initially_relevant('according_to(r34_4,may(LP,accept,EA))',rules)))