#!/bin/env python3

eol = '$'
epsilon = 'epsilon'

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

    def next(self):
        return self.la if self.dot == len(self.rhs) else self.rhs[self.dot]

    def __str__(self):
        retstr = self.lhs + " -> "
        for i in range(0, len(self.rhs)):
            if i == self.dot:
                retstr += "• "
            retstr +=  self.rhs[i] + " "
        if self.dot == len(self.rhs):
            retstr += "•"

        return retstr + "{{{}}}".format(self.la)

    def __eq__(self, other):
        if not isinstance(other, LR1_Prod):
            return False
        return self.lhs == other.lhs and self.rhs == other.rhs and self.dot == other.dot and self.la == other.la

    def __hash__(self):

        h = hash("{}{}{}{}".format(self.lhs,self.rhs, self.dot, self.la))

        return h

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
            if p in finSymbols:
                continue

            currSymbols.add(p)
            finSymbols.add(p)

        while currSymbols:
            currSym = currSymbols.pop()
            for prod in [p for p in pi.productions if p.lhs == currSym.next()]:
                temp = prod.to_LR1()
                
                #TODO find la
                self.lr1_prods.add(temp)
                if not temp in finSymbols:
                    if temp.lhs in pi.nonterminals:
                        finSymbols.add(temp)
                        currSymbols.add(temp)

    def __str__(self):
        return "State {}:\n\n".format(self.id) + "\n".join(map(str, self.lr1_prods))

class CLR_Parser:
    def __init__(self, grammar, startsymbol, terminals):
        terminals |= {epsilon}

        #calc productions
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


        #calc first sets TODO epsilon
        firsts = dict([(x, [{x} if x in pi.terminals else set(), set() if x in pi.terminals else {x}]) for x in pi.terminals | pi.nonterminals])

        for p in pi.productions:
            counter = 0
            while True:
                currSym = p.rhs[counter]
                firsts[p.lhs][0 if currSym in pi.terminals else 1].add(currSym)
                if currSym is not epsilon:
                    break

                counter += 1
                if counter >= len(p.rhs):
                    break


        eclipsable = set([x for x in firsts.keys() if epsilon in firsts[x][0]])


        while True:
            updated = False

            for prod in pi.productions:
                broken = False
                for rh in prod.rhs:
                    if not all([p in firsts[prod.lhs][0] for p in firsts[rh][0] if not p == epsilon]):
                        firsts[prod.lhs][0] |= firsts[rh][0] - { epsilon }
                        updated = True
                    #TODO remove
                    if not all([p in firsts[prod.lhs][1] for p in firsts[rh][1]]):
                        firsts[prod.lhs][1] |= firsts[rh][1]
                        updated = True
                    if not rh in eclipsable:
                        broken = True
                        break
                if not broken:
                    eclipsable |= { prod.lhs }
                    firsts[prod.lhs][0] |= {epsilon}
                    

            if not updated:
                break

        pi.firsts = dict([(x, y[0]) for x, y in firsts.items()])
        print(pi.firsts)

        print("\nFirst-Sets:\n")
        for k, v in [p for p in pi.firsts.items() if not p[0] in pi.terminals]:
            print("First({}): {}".format(k, v))



        print("\nStates:\n")

        states = [CLR_State(pi, {LR1_Prod('S\'', [startsymbol], eol, 0)})]

        print(states[0])


        print("\n" * 5)


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
        F -> f | epsilon""", 'S', {'a', 'b', 'c', 'f', 'g'})
