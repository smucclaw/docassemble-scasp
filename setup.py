import os
import sys
from setuptools import setup, find_packages
from fnmatch import fnmatchcase
from distutils.util import convert_path

standard_exclude = ('*.pyc', '*~', '.*', '*.bak', '*.swp*')
standard_exclude_directories = ('.*', 'CVS', '_darcs', './build', './dist', 'EGG-INFO', '*.egg-info')
def find_package_data(where='.', package='', exclude=standard_exclude, exclude_directories=standard_exclude_directories):
    out = {}
    stack = [(convert_path(where), '', package)]
    while stack:
        where, prefix, package = stack.pop(0)
        for name in os.listdir(where):
            fn = os.path.join(where, name)
            if os.path.isdir(fn):
                bad_name = False
                for pattern in exclude_directories:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                if os.path.isfile(os.path.join(fn, '__init__.py')):
                    if not package:
                        new_package = name
                    else:
                        new_package = package + '.' + name
                        stack.append((fn, '', new_package))
                else:
                    stack.append((fn, prefix + name + '/', package))
            else:
                bad_name = False
                for pattern in exclude:
                    if (fnmatchcase(name, pattern)
                        or fn.lower() == pattern.lower()):
                        bad_name = True
                        break
                if bad_name:
                    continue
                out.setdefault(package, []).append(prefix+name)
    return out

setup(name='docassemble.scasp',
      version='0.0.1',
      description=('A docassemble extension to allow access to the send queries to an s(CASP) reasoner and display the responses.'),
      long_description='# docassemble-scasp\r\n\r\nThis package provides python access to an s(CASP) reasoner installed on your docassemble server, and an interface for displaying the results of an s(CASP)\r\nquery inside a docassemble interview.\r\n\r\n[s(CASP)](https://gitlab.software.imdea.org/ciao-lang/sCASP) is a stable-model constraint answer set programming tool which is very useful for encoding legal rules.\r\n\r\n## Installation\r\n\r\nInside the docassemble server, [install the package from its github repository](https://docassemble.org/docs/packages.html#github_install).\r\n\r\nYou must also have s(CASP) installed on your docassemble container. Instructions for installing s(CASP) are [avaialble here](https://gitlab.software.imdea.org/ciao-lang/sCASP).\r\n\r\n## Configuration\r\n\r\nIn the docassemble global configuration, add the following lines:\r\n\r\n```\r\nscasp:\r\n  location: /path/to/scasp\r\n```\r\n\r\nIf you do not have these lines in your configuration, it will presume that scasp is installed at `/var/www/.ciao/build/bin/scasp`.\r\n\r\n## Testing\r\n\r\nIt should create an interview called \'DAScasp_test.yml\'. Run that interview, and it should generate the following screen:\r\n\r\n## Usage\r\n\r\nOnce you have the package installed, you can use s(CASP) inside your docassemble\r\ninterviews by doing the following things:\r\n\r\n### Include DAScasp.yml\r\n\r\nIn your docassemble interview, add the following lines:\r\n\r\n```\r\ninclude:\r\n  - DAScasp.yml\r\n```\r\n\r\n### Specify a Rule Source, and a Query\r\n\r\nThe s(CASP) reasoner needs the name of an s(CASP) file (extension `.pl`) in\r\nthe static folder that sets out the rules that should be queried against.\r\nIt also needs a valid s(CASP) query.  Those should be set out as follows:\r\n\r\n```\r\n---\r\nmandatory: True\r\ncode: |\r\n  ruleSource = "mortal.pl"\r\n  query = "mortal(X)."\r\n---\r\n```\r\n\r\n### Specify Facts\r\n\r\nIf you want to add information provided by the user of your interview to your\r\ns(CASP) encoding prior to running the query, you need to take that data and\r\nadd it to the `facts` variable.\r\n\r\nFor example:\r\n\r\n```\r\n---\r\nmandatory: True\r\ncode: |\r\n  facts = ""\r\n  for p in person:\r\n    facts += "human( " + p.instance_name + ").\\n"\r\n---\r\n```\r\n\r\n### Display the Answer\r\n\r\nIn your interview, display `DAScasp_show_answers`.\r\n\r\n```\r\n---\r\nquestion: result\r\nsubquestion: |\r\n  ${ DAScasp_show_answers}\r\n---\r\n```\r\n\r\n### Customizing\r\n\r\n#### Changing the number of answers displayed\r\n\r\nBy default, DAScasp is configured to display only the first answer returned by the s(CASP) reasoner. If you would like to display a larger number, you can set the value of `scasp_number` to that number. If you would like to display all answers, you can set the value of `scasp_number` to `0`.\r\n\r\n```\r\ncode: |\r\n  scasp_number = 0 # Will display all answers\r\n```\r\n\r\n#### Changing whether models are displayed\r\n\r\nBy default, DAScasp does not display models associated with answers. If you would like to display models in addition to bindings and justifications, you\r\ncan set `show_models` to `True`.\r\n\r\n```\r\ncode: |\r\n  show_models = True # Will cause models to be displayed in answers.\r\n```',
      long_description_content_type='text/markdown',
      author='Jason Morris',
      author_email='jmorris@smu.edu.sg',
      license='',
      url='https://docassemble.org',
      packages=find_packages(),
      namespace_packages=['docassemble'],
      install_requires=[],
      zip_safe=False,
      package_data=find_package_data(where='docassemble/scasp/', package='docassemble.scasp'),
     )

