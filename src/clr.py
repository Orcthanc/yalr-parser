#!/bin/env python3

eol = '$'

class TempParserInternals:
    def __init__(self):
        self.terminals = set()
        self.nonterminals = set()
        self.productions = []
        self.firsts = {}
        self.stateid = 0

class Production:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def to_LR1(self):
        return LR1_Prod(self.lhs, self.rhs, eol, 0)

    def __str__(self):
        return self.lhs + " -> " + " ".join(self.rhs)

class LR1_Prod(Production):
    def __init__(self, lhs, rhs, la, dot):
        super().__init__(lhs, rhs)
        self.la = la
        self.dot = dot

    def __str__(self):
        retstr = self.lhs + " -> "
        for i in range(0, len(self.rhs)):
            if i == self.dot:
                retstr += "• "
            retstr +=  self.rhs[i] + " "
        if self.dot == len(self.rhs):
            retstr += "•"

        return retstr + "{{{}}}".format(self.la)

class CLR_State:
    def __init__(self, pi, lr1_prods):
        self.lr1_prods = set()
        self.id = pi.stateid
        pi.stateid += 1

        currSymbols = set()
        finSymbols = set()
        for p in lr1_prods:
            self.lr1_prods |= {p}
            symbol = p.rhs[p.dot]
            if symbol in finSymbols:
                continue

            currSymbols.add(symbol)
            finSymbols.add(symbol)

        while currSymbols:
            currSym = currSymbols.pop()
            for prod in [p for p in pi.productions if p.lhs == currSym]:
                temp = prod.to_LR1()
                #TODO find la
                self.lr1_prods.add(temp)
                if prod.rhs[0] in pi.nonterminals:
                    if not prod.rhs[0] in finSymbols:
                        finSymbols.add(prod.rhs[0])
                        currSymbols.add(prod.rhs[0])

    def __str__(self):
        return "State {}:\n\n".format(self.id) + "\n".join(map(str, self.lr1_prods))

class CLR_Parser:
    def __init__(self, grammar, startsymbol, terminals):

        pi = TempParserInternals()

        print("Startsymbol: {}\n".format(startsymbol))

        for line in grammar.splitlines():
            arrow = line.split('->')
            lhs = arrow[0].strip()
            pi.nonterminals |= {lhs}
            for option in arrow[1].split('|'):
                rhs = [x.strip() for x in option.split()]
                pi.nonterminals |= set(rhs)
                pi.productions.append(Production(lhs, rhs))

        pi.nonterminals -= terminals

        pi.terminals = terminals

        print("Terminals: " + ", ".join(pi.terminals) + "\n")

        print("Nonterminals: " + ", ".join(pi.nonterminals) + "\n")

        pi.productions = sorted(pi.productions, key = lambda x: (x.lhs, x.rhs))

        print("Grammar:\n")
        for p in pi.productions:
            print( p )

        print("\nStates:\n")

        states = []
        states.append(CLR_State(pi, {LR1_Prod('S\'', [startsymbol], eol, 0)}))

        print(states[0])


if __name__ == '__main__':
    
    CLR_Parser("""T -> ( E ) | T * T
        E -> E + E | T
        T -> i""", 'E', {'i', '*', '(', ')', '+'})
