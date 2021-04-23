# docassemble-scasp

This package provides python access to an s(CASP) reasoner installed on your docassemble server, and an interface for displaying the results of an s(CASP)
query inside a docassemble interview.

[s(CASP)](https://gitlab.software.imdea.org/ciao-lang/sCASP) is a stable-model constraint answer set programming tool which is very useful for encoding legal rules.

## Installation

Inside the docassemble server, [install the package from its github repository](https://docassemble.org/docs/packages.html#github_install).

You must also have s(CASP) installed on your docassemble container. Instructions for installing s(CASP) are [avaialble here](https://gitlab.software.imdea.org/ciao-lang/sCASP).

(Or, do it the easy way, and install an image of docassemble with s(CASP) and this module
already installed, [available here](https://github.com/smucclaw/l4-docassemble))

## Configuration

In the docassemble global configuration, add the following lines:

```
scasp:
  location: /path/to/scasp
```

If you do not have these lines in your configuration, it will presume that scasp is installed at `/var/www/.ciao/build/bin/scasp`.

## Testing

It should create an interview called 'DAScasp_test.yml'. Run that interview by going to the following address, replacing your host name
as appropriate: `http://localhost/interview?i=docassemble.scasp:DAScasp_test.yml`. You should see an answer that answers that Socrates is mortal
and explains why.

## Usage

Once you have the package installed, you can use s(CASP) inside your docassemble
interviews by doing the following things:

### Include DAScasp.yml

In your docassemble interview, add the following lines:

```
include:
  - docassemble.scasp:DAScasp.yml
```

(Note that if you have loaded DAScasp into your docassemble playground, and not installed on your docassemble server, the syntax for
including the DAScasp.yml file does not require the package name.)

### Specify a Rule Source, and a Query

The s(CASP) reasoner needs the name of an s(CASP) file (extension `.pl`) in
the static folder that sets out the rules that should be queried against.
It also needs a valid s(CASP) query.  Those should be set out as follows:

```
---
mandatory: True
code: |
  ruleSource = "mortal.pl"
  query = "mortal(X)."
---
```

### Specify Facts

If you want to add information provided by the user of your interview to your
s(CASP) encoding prior to running the query, you need to take that data and
add it to the `facts` variable.

For example:

```
---
mandatory: True
code: |
  facts = ""
  for p in person:
    facts += "human( " + p.instance_name + ").\n"
---
```

### Display the Answer

In your interview, display `DAScasp_show_answers`.

```
---
question: result
subquestion: |
  ${ DAScasp_show_answers}
---
```

### Customizing

#### Changing the number of answers displayed

By default, DAScasp is configured to display only the first answer returned by the s(CASP) reasoner. If you would like to display a larger number, you can set the value of `scasp_number` to that number. If you would like to display all answers, you can set the value of `scasp_number` to `0`.

```
code: |
  scasp_number = 0 # Will display all answers
```

#### Changing whether models are displayed

By default, DAScasp does not display models associated with answers. If you would like to display models in addition to bindings and justifications, you
can set `show_models` to `True`.

```
code: |
  show_models = True # Will cause models to be displayed in answers.
```
