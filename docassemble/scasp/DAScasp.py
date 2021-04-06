# A simple interface to the s(CASP) constraint answer set programming
# tool from inside a Docassemble interview.

import string
import os
import subprocess
import urllib.parse
import re
from docassemble.base.functions import get_config
from docassemble.base.core import DAFile


# FOR TESTING ONLY
#import yaml
#data_structure_file = open('data/static/mortal.yml',"r")
#data_structure = yaml.load(data_structure_file,Loader=yaml.FullLoader)
#query = "?- mortal(X)."
#rules = "#pred mortal(X) :: '@(X) is mortal'.\n#pred human(X) :: '@(X) is human'.\n#pred other(X) :: '@(X) is other'.\nmortal(X) :- human(X).\nmortal(X) :- other(X)."


# Send an s(CASP) file to the reasoner and return the results.
def sendQuery(filename, number=0):
    number_flag = "-s" + str(number)
    scasp_location = get_config('scasp')['location'] if (get_config('scasp') and get_config('scasp')['location']) else '/var/www/.ciao/build/bin/scasp'
    #scasp_location = 'scasp'
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

def get_predicates(input):
    predicates = []
    predicate = re.compile(r"^\#pred ([^\s]*) :: ", re.M)
    for p in predicate.finditer(input):
        predicates.append(generalize_predicate(p.group(1)))
    return predicates

def get_rule_conclusions(input):
    conclusions = set()
    rule = re.compile(r"^([^\s]*) \:\- .*", re.M)
    for r in rule.finditer(input):
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
    #code.write(query)
    # Save the file
    code.write(content)
    #code.close()
    # Run the code
    results = sendQuery(code.path())
    # Take the union of all of the predicates in all of the answers
    # that are not conclusions
    relevant = set()
    conclusions = get_rule_conclusions(rules)
    for a in results['answers']:
        for p in a['model']:
            if generalize_predicate(p) not in conclusions:
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
    predicate_parts = re.compile(r"([^\(]*)(?:\(([^\)]*)\)){0,1}")
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

# OK, ds2dal4 has been updated. It is now expecting docassemble.scasp to provide
# two functions, generate_agenda() and generate_subagenda().
# agenda is a list of the root elements that should be collected.
# subagenda is a list of the subelements that should be collected. The current
# relevance list might be sufficient for subagenda. We need to find roots and
# collect them for the agenda.

# There are also going to be bugs in the relevance code that will be revealed
# by the more complicated interview, undoubtedly. Let's go.

def generate_agenda():
    output = []
    output.append('legal_practice.gather()')
    return output

def generate_subagenda(rules,query,data_structure):
    rel = get_relevant(rules,query)
    agenda = []
    for r in rel:
        for d in data_structure['data']:
            target = find_element_for_encoding(d,expand_predicate(r))
            if target:
                agenda.append(add_index(target))
    return agenda
    #output.append('legal_practice[i].value')
    #output.append('legal_practice[i].joint_law_venture.value')
    #return output