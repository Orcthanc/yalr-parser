#!/bin/env python3

import ply.lex as lex

tokens = ( 'INTL', 'PLUS', 'TIMES' )

t_PLUS = r'\+'
t_TIMES = r'\*'
t_INTL = r'\d+'

def t_error(t):
    print("Illegal character {}".format(t.value))

lexer = lex.lex()

while True:
    lexer.input(input("> "))
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
