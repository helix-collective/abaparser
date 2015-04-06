# ABA Parser/Reporter in Python #

ABA (Australian Bankers Association or Cemtext file format) is the standard format all Australian online banks accept. This is an archaic fixed file format, and it's hard to eye-ball for correctness.

This script serves currently serves 2 purposes

 1. A python library to parse ABA files.
 2. A basic command line report of all the debit transactions in the ABA file (I use this to sanity check payments out of Xero)

## Install ##

I'd recommend just checking out the git repo (it's a small python file). However,
it is all pip compatible so the usual
```
$ virtual pyenv
$ source pyenv/bin/activate
$ pip install abaparser
```

## Usage ##
`
$ python -m abaparser < path/to/FILE.ABA
`

The output will be something like this

```
Contractors
012-327	293353749	John Doe	Contractor Payment	1220.00
082-406	598209320	Jane Doe	Contractor Payment	6600.00
```
