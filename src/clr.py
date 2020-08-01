#!/bin/env python3

import copy
from enum import Enum

eol = '$'
epsilon = 'epsilon'

class SRG(Enum):
    SHIFT = 0
    REDUCE = 1
    GOTO = 2

class Action:
    def __init__(self, action, number):
        self.action = action
        self.number = number

    def __repr__(self):
        return "({} {})".format(self.action, self.number)

class TempParserInternals:
    def __init__(self):
        self.terminals = set()
        self.nonterminals = set()
        self.productions = []
        self.firsts = {}
        self.stateid = 0
        self.table = []

class Production:
    def __init__(self, lhs, rhs, Id):
        self.lhs = lhs
        self.rhs = rhs
        self.Id = Id

    def to_LR1(self):
        return LR1_Prod(self.lhs, self.rhs, self.Id, set(), 0)

    def __str__(self):
        return self.lhs + " -> " + " ".join(self.rhs)

class LR1_Prod(Production):
    def __init__(self, lhs, rhs, Id, la, dot):
        super().__init__(lhs, [r for r in rhs if not r == epsilon], Id)
        self.la = la
        self.dot = dot

    def next(self, amount):
        return self.la if self.dot + amount == len(self.rhs) else {self.rhs[self.dot + amount]}

    def __str__(self):
        retstr = self.lhs + " -> "
        for i in range(0, len(self.rhs)):
            if i == self.dot:
                retstr += "• "
            retstr +=  self.rhs[i] + " "
        if self.dot == len(self.rhs):
            retstr += "•"

        return retstr + "{}".format(self.la)

    def __repr__(self):
        retstr = self.lhs + " -> "
        for i in range(0, len(self.rhs)):
            if i == self.dot:
                retstr += "• "
            retstr +=  self.rhs[i] + " "
        if self.dot == len(self.rhs):
            retstr += "•"

        return retstr + "{}".format(self.la)

    def canBeMerged(self, other):
        return self.lhs == other.lhs and self.rhs == other.rhs and self.dot == other.dot

    def final(self):
        return self.dot == len(self.rhs)

    def __eq__(self, other):
        if not isinstance(other, LR1_Prod):
            return False
        return self.lhs == other.lhs and self.rhs == other.rhs and self.dot == other.dot and self.la == other.la

    def __hash__(self):

        h = hash("{}{}{}".format(self.lhs,self.rhs, self.dot))

        return h

class CLR_State:
    def __init__(self, pi, lr1_prods):
        self.lr1_prods = set()
        self.id = pi.stateid

        currSymbols = set()
        finSymbols = set()
        for p in lr1_prods:
            self.lr1_prods |= {p}
            if p.dot >= len(p.rhs):
                continue
            symbol = p.rhs[p.dot]
            if p in finSymbols:
                continue

            currSymbols.add(p)
            finSymbols.add(p)

        while currSymbols:
            currSym = currSymbols.pop()
            for prod in [p for p in pi.productions if p.lhs in currSym.next(0)]:
                temp = prod.to_LR1()
                for s in currSym.next(1):
                    temp.la |= pi.firsts[s]
                for lah in [x for x in self.lr1_prods if temp.canBeMerged(x)]:
                    temp.la |= lah.la
                    self.lr1_prods.discard(lah)
                self.lr1_prods.add(temp)
                if not temp in finSymbols:
                    if temp.lhs in pi.nonterminals:
                        finSymbols.add(temp)
                        currSymbols.add(temp)

    def getNextProds(self, nextSymbol):
        temp = [copy.deepcopy(p) for p in self.lr1_prods if nextSymbol in p.next(0) and not p.dot == len(p.rhs)]
        for p in temp:
            p.dot += 1
        return temp

    def reduceSet(self):
        prods = [p for p in self.lr1_prods if p.final()]
        return prods

    def __eq__(self, other):
        if not isinstance(other, CLR_State):
            return False
        if not len(self.lr1_prods) == len(other.lr1_prods):
            return False
        if not self.lr1_prods >= other.lr1_prods:
            return False
        return True

    def __str__(self):
        return "State {}:\n\n".format(self.id) + "\n".join(map(str, self.lr1_prods))

class CLR_Parser:
    def __init__(self, grammar, startsymbol, terminals):
        terminals |= {epsilon}

        #calc productions
        pi = TempParserInternals()

        print("Startsymbol: {}\n".format(startsymbol))

        ProdId = 1
        for line in grammar.splitlines():
            arrow = line.split('->')
            lhs = arrow[0].strip()
            pi.nonterminals |= {lhs}
            for option in arrow[1].split('|'):
                rhs = [x.strip() for x in option.split()]
                pi.nonterminals |= set(rhs)
                pi.productions.append(Production(lhs, rhs, ProdId))
                ProdId += 1

        pi.nonterminals -= terminals

        pi.terminals = terminals

        print("Terminals: ", pi.terminals, "\n")

        print("Nonterminals: ", pi.nonterminals, "\n")

        pi.productions = sorted(pi.productions, key = lambda x: (x.lhs, x.rhs))

        print("Grammar:\n")
        for p in pi.productions:
            print( p )


        #calc first sets
        pi.firsts = dict([(x, {x} if x in pi.terminals else set()) for x in pi.terminals | pi.nonterminals])

        pi.firsts[eol] = {eol}

        for p in pi.productions:
            counter = 0
            while True:
                currSym = p.rhs[counter]
                if currSym in pi.terminals:
                    pi.firsts[p.lhs].add(currSym)
                if currSym is not epsilon:
                    break

                counter += 1
                if counter >= len(p.rhs):
                    break


        eclipsable = set([x for x in pi.firsts.keys() if epsilon in pi.firsts[x]])


        while True:
            updated = False

            for prod in pi.productions:
                broken = False
                for rh in prod.rhs:
                    if not all([p in pi.firsts[prod.lhs] for p in pi.firsts[rh] if not p == epsilon]):
                        pi.firsts[prod.lhs] |= pi.firsts[rh] - { epsilon }
                        updated = True
                    if not rh in eclipsable:
                        broken = True
                        break
                if not broken:
                    eclipsable |= { prod.lhs }
                    pi.firsts[prod.lhs] |= {epsilon}


            if not updated:
                break

        print("\nFirst-Sets:\n")
        for k, v in [p for p in pi.firsts.items() if not p[0] in pi.terminals]:
            print("First({}): {}".format(k, v))



        print("\nStates:\n")

        states = [CLR_State(pi, {LR1_Prod('S\'', [startsymbol], 0, {eol}, 0)})]

        pi.stateid += 1

        counter = 0

        while True:
            currId = states[counter].id
            for sym in pi.terminals | pi.nonterminals - { epsilon }:
                temp = states[counter].getNextProds(sym)
                if temp:
                    targetId = -1
                    newstate = CLR_State(pi, temp)
                    existing = [p for p in states if p == newstate]
                    if not existing:
                        pi.stateid += 1
                        states.append(newstate)
                        targetId = pi.stateid
                    else:
                        targetId = existing[0].id
                    if currId >= len(pi.table):
                        pi.table.append(dict())
                    pi.table[currId][sym] = Action(SRG.SHIFT if sym in pi.terminals else SRG.GOTO, targetId)

            temp = states[counter].reduceSet()
            for rule in temp:
                if currId >= len(pi.table):
                    pi.table.append(dict())
                for s in rule.la:
                    if s in pi.table[currId]:
                            if pi.table[currId][s].action == SRG.SHIFT:
                                print("Shift-Reduce conflict in state {} for symbol {}".format(currId, s))
                                continue
                            else:
                                print("Reduce-reduce conflict in state {} for rules {} and {} with symbol {}".format(currId, pi.table[currId][s].number, rule.Id, s))
                    pi.table[currId][s] = Action(SRG.REDUCE, rule.Id)

            counter += 1
            if counter == len(states):
                break

        for s in states:
            print(s, "\n")

        print("\nTable:\n")

        for k in range(0, len(pi.table)):
            print(k, pi.table[k])
        #print(pi.table)


        print("\n" * 5)

        self.table = pi.table


if __name__ == '__main__':

    CLR_Parser("""T -> ( E ) | T * T
        E -> E + E | T
        T -> i""", 'E', {'i', '*', '(', ')', '+'})


    CLR_Parser("""S -> A A
    A -> a A | b""", 'S', {'a', 'b'})


    CLR_Parser("""S -> S X | Y
    X -> x | epsilon
    Y -> y | epsilon""", 'S', {'x', 'y'})


    CLR_Parser("""S -> a B D h
        B -> c C
        C -> b C | epsilon
        D -> E F
        E -> g | epsilon
        F -> f | epsilon""", 'S', {'a', 'b', 'c', 'f', 'g', 'h'})

    CLR_Parser("""S -> ( S ) | S , S | epsilon""", 'S', {'(', ')', ','})

    CLR_Parser("""S -> S + S | a""", 'S', {'a', '+'})
