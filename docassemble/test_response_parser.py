import docassemble.scasp.responseparser as rp
from docassemble.scasp.responseparser import *

for file in ['example_disunity.txt','example_model.txt','example_no_bindings.txt','example_no_model.txt']:
    responsefile = open('docassemble/scasp/data/static/' + file, 'r')
    code = responsefile.read()
    parse = response.parseString(code,True)
    print(parse.dump())
