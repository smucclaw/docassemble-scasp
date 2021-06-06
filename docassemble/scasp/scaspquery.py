# This script takes the name of an operating system file that is an s(CASP)
# program and includes a query, sends that query to the s(CASP) reasoner,
# and then returns a result that is designed to be displayed inside
# a docassemble interview.

# Because it returns docassemble-specific content, and because it gets the
# name of the location of the scasp reasoner from the docassemble configuration
# it belongs in docassemble-scasp

import subprocess
import re
import urllib.parse
no_docassemble = False
try:
    from docassemble.base.functions import get_config
except ModuleNotFoundError:
    no_docassemble = True


# Send an s(CASP) file to the scasp reasoner and return the results.
def sendQuery(filename, number=0, human=True):
    number_flag = "-s" + str(number)
    if human:
        human_flag = "--human"
    else:
        human_flag = ""
    if no_docassemble:
        scasp_location = "scasp"
    else:
        scasp_location = get_config('scasp')['location'] if (get_config('scasp') and get_config('scasp')['location']) else '/var/www/.ciao/build/bin/scasp'
    results = subprocess.run([scasp_location, human_flag, '--tree', number_flag, filename], capture_output=True).stdout.decode('utf-8')
    
    pattern = re.compile(r"daSCASP_([^),\s]*)")
    matches = list(pattern.finditer(results))
    for m in matches:
        results = results.replace(m.group(0),urllib.parse.unquote_plus(m.group(1).replace('__perc__','%').replace('__plus__','+')))
    return process_output(results)


def process_output(results):
    output = {}

    # If result is no models
    if results.endswith('no models\n\n'):
        query = results.replace('\n\nno models\n\n','').replace('\n    ','').replace('QUERY:','').replace('{','').replace('}','').replace('% ','')
        output['query'] = query
        output['result'] = 'No'
        return output
    else:
        # Divide up the remainder into individual answers
        answers = results.split("\tANSWER:\t")
        query = answers[0]
        del answers[0]
        query = query.replace('\n','').replace('     ',' ').replace('QUERY:','').replace('% ','').replace('{','').replace('}','')
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
            explanations = make_tree_list(tree)
            explanations = display_list_from_lists(explanations)

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
        
        # Reorganize the tree so that bindings are a level above models and explanations.
        
        new_output = {}
        new_output['query'] = output['query']
        new_output['result'] = output['result']
        new_output['answers'] = []
        for a in output['answers']:
            present = False
            for na in new_output['answers']:
                if a['bindings'].sort() == na['bindings'].sort():
                    present = True
            if not present:
                new_output['answers'].append({'bindings': a['bindings'], 'models': []})
        for a in output['answers']:
            for na in new_output['answers']:
                if a['bindings'] == na['bindings']:
                    na['models'].append({'time': a['time'], 'model': a['model'], 'explanations': a['explanations']})
                    # na['models']['time'] = a['time']
                    # na['models']['model'] = a['model']
                    # na['models']['explanations'] = a['explanations']
        
        for i in range(len(new_output['answers'])):
            nlg_answer = new_output['query']
            nlg_answer = nlg_answer.replace('I would like to know if ','')
            for b in new_output['answers'][i]['bindings']:
                splitbinding = b.split(': ')
                if len(splitbinding) > 1:
                    nlg_answer = nlg_answer.replace(splitbinding[0],splitbinding[1])
            new_output['answers'][i]['nlg_answer'] = nlg_answer
        
        return new_output

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


def get_depths_list(lines):
    stack = [[]]
    for l in lines:
        # If we get to global constraints, stop.
        if l.startswith('The global constraints hold'):
            break
        # Skip lines that start with 'abducible' holds
        if l.lstrip(' ').startswith('\'abducible\' holds'):
            continue

        current_line_depth = (len(l) - len(l.lstrip(' ')))//4
        tree_depth = len(stack) - 1

        if current_line_depth > tree_depth:
            new_level = []
            stack[-1].append(new_level)
            stack.append(new_level)

        if current_line_depth < tree_depth:
            for i in range(tree_depth-current_line_depth):  # Unwind stack
                stack.pop()

        current_list = stack[-1]  # peek

        line_text = l.lstrip(' ')

        # s(CASP) applies periods to some lines that we don't display, so
        # just get rid of them all.
        if line_text.endswith('.'):
            line_text = line_text.rstrip('.')

        current_list.append(line_text)
    return stack[0]


def make_tree(lines):
    # Add depth information to the lines
    lines = lines.splitlines()
    meta_lines = get_depths(lines)

    return meta_lines


def make_tree_list(lines):
    lines = lines.splitlines()
    meta_lines = get_depths_list(lines)

    return meta_lines

def display_list(input,depth=0):
    #print(("    " * int(depth)) + "Processing a list of length " + str(len(input)) + ", starting with " + input[0]['text'] + " at depth " + str(depth) + "." )
    if depth==0:
        #print("<ul id=\"explanation\" class=\"active\">")
        output = "<ul id=\"explanation\" class=\"active\">"
    else:

        #print("<ul class=\"nested\">")
        output = "<ul class=\"nested\">"
    #print(("    " * int(depth)) + "Setting the number of lines to skip to zero.")

    skip = 0
    #print(("    " * int(depth)) + "Going through the lines.")
    for i in range(len(input)):
        #print(("    " * int(depth)) + "Working on line " + str(i) + ", \"" + input[i]['text'] + " at depth " + str(input[i]['depth']) + ".")
        if skip > 0:
            #print(("    " * int(depth)) + "Skipping.")
            skip = skip-1
            #print(("    " * int(depth)) + "Skips remaining: " + str(skip) + ".")
            continue

        if input[i]['depth'] == depth:
            #print(("    " * int(depth)) + "This line is at the right depth, adding it.")
            if input[i]['text'].endswith('because'):
                #print(("    " * int(depth)) + "This line has children.")
                #print("<li><span class=\"caret\">")
                output += "<li><span class=\"caret\">"
            else:
                #print(("    " * int(depth)) + "This line does not have children.")
                #print("<li>")
                output += "<li>"
            #print(input[i]['text'])
            output += input[i]['text']
            if input[i]['text'].endswith('because'):

                #print("</span>")

                output += "</span>"
            else:
                #print("</li>")
                output += "</li>"

        if input[i]['depth'] > depth:
            #print(("    " * int(depth)) + "This line is deeper.")
            sub_output = display_list(input[i:],input[i]['depth'])
            skip = sub_output.count("<li>")-1 # skip the parts already done.
            #print(("    " * int(depth)) + "Setting the number of lines to skip to " + str(skip) + ".")
            output += sub_output
        if input[i]['depth'] < depth:
            #print(("    " * int(depth)) + "This line is shallower.")
            #print("</ul>")
            #output += "</ul>"
            output += "</ul></li>"
            return output
            #depth = depth-1
            #print(("    " * int(depth)) + "Resetting depth to " + str(depth) + ".")
    
    output += "</ul>"
    if depth != 0:
        output += "</li>"
    return output


def display_list_from_lists(input, top_level=True, ul_attrs="id=\"explanation\" class=\"active\""):
    output = f"<ul {ul_attrs}>"

    for i in range(len(input)):
        if isinstance(input[i], str):
            if input[i].endswith('because'):
                output += "<li><span class=\"caret\">"
            else:
                output += "<li>"
            output += input[i]
            if input[i].endswith('because'):
                output += "</span>"
            else:
                output += "</li>"

        if isinstance(input[i], list):
            sub_output = display_list_from_lists(input[i], False, "class=\"nested\"")
            output += sub_output
            output += "</li>"

    output += "</ul>"
    return output
