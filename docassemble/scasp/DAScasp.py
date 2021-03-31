# A simple interface to the s(CASP) constraint answer set programming
# tool from inside a Docassemble interview.

import subprocess
import urllib.parse
import re
from docassemble.base.functions import get_config
from docassemble.base.util import log

# Send an s(CASP) file to the reasoner and return the results.
def sendQuery(filename, number=0):
    number_flag = "-s" + str(number)
    scasp_location = get_config('scasp')['location'] if (get_config('scasp') and get_config('scasp')['location']) else '/var/www/.ciao/build/bin/scasp'
    results = subprocess.run([scasp_location, '--human', '--tree', number_flag, filename], capture_output=True).stdout.decode('utf-8')
    log(results, "info")
    pattern = re.compile(r"daSCASP_([^),\s]*)")
    matches = list(pattern.finditer(results))
    for m in matches:
        results = results.replace(m.group(0),urllib.parse.unquote_plus(m.group(1).replace('__perc__','%').replace('__plus__','+')))
    log(results, "info")
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

def unencode(string):
    # For every string starting with daSCASP_ until space or punctuation
    # remove the daSCASP, replace each instance of __perc__ with a % sign,
    # then urllib.parse.unquote_plus() it to get back the orignal content.

    pass

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