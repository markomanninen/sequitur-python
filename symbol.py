
class Symbol(object):
    """docstring for Symbol"""
    def __init__(self, value, grammar):
        from rule import Rule
        super(Symbol, self).__init__()
        self.grammar = grammar
        self.next = None
        self.prev = None
        self.terminal = None
        self.rule = None
        
        if (str == type(value)):
            self.terminal = value
        elif (Symbol == type(value)):
            if value.terminal:
                self.terminal = value.terminal
            elif value.rule:
                self.rule = value.rule
                self.rule.increment_reference_count()
        elif (Rule == type(value)):
            self.rule = value
            self.rule.increment_reference_count()
        else:
            print "Did not recognize %s" % value

    def join(self, right):
        """
        Links two symbols together, removing any old digram from the hash table.
        """
        if (self.next):
            self.delete_digram()
            
            """
            This is to deal with triples, where we only record the second
            pair of overlapping digrams. When we delete the second pair,
            we insert the first pair into the hash table so that we don't
            forget about it. e.g. abbbabcbb
            """
            
            if ((right.prev is not None) and (right.next is not None) and
                right.value() == right.prev.value() and
                right.value() == right.next.value()):
                self.grammar.add_index(right)
            if ((self.prev is not None) and (self.next is not None) and
                self.value() == self.next.value() and
                self.value() == self.prev.value()):
                self.grammar.add_index(self)
        self.next = right
        right.prev = self

    def delete(self):
        """
        Cleans up for symbol deletion: removes hash table entry and decrements
        rule reference count.
        """
        self.prev.join(self.next)
        if not self.is_guard():
            self.delete_digram()
            if self.rule:
                self.rule.decrement_reference_count()

    def delete_digram(self):
        """Removes the digram from the hash table"""
        if (self.is_guard() or self.next.is_guard()):
            return
        
        self.grammar.clear_index(self)

    def insert_after(self, symbol):
        """Inserts a symbol after this one"""
        symbol.join(self.next)
        self.join(symbol)

    def is_guard(self):
        """
        Returns true if this is the guard node marking the beginning and end of 
        a rule.
        """
        return self.rule and (self.rule.first().prev == self)

    def check(self):
        """
        Checks a new digram. If it appears elsewhere, deals with it by 
        calling match(), otherwise inserts it into the hash table
        """
        if (self.is_guard() or self.next.is_guard()):
            return None
        match = self.grammar.get_index(self)
        if not match:
            self.grammar.add_index(self)
            return False
        if match.next != self:
            self.process_match(match)
        return True

    def expand(self):
        """
        This symbol is the last reference to its rule. It is deleted, and the
        contents of the rule substituted in its place.
        """
        left = self.prev
        right = self.next
        first = self.rule.first()
        last = self.rule.last()
        
        self.grammar.clear_index(self)
        left.join(first)
        last.join(right)
        self.grammar.add_index(last)

    def substitute(self, rule):
        """Replace a digram with a non-terminal"""
        prev = self.prev
        prev.next.delete()
        prev.next.delete()
        prev.insert_after(Symbol(rule, self.grammar))
        if not prev.check():
            prev.next.check()

    def process_match(self, match):
        """Deal with a matching digram"""
        from rule import Rule
        rule = None
        if (match.prev.is_guard() and match.next.next.is_guard()):
            # reuse an existing rule
            rule = match.prev.rule
            self.substitute(rule)
        else:
            # create a new rule
            rule = Rule(self.grammar)
            rule.last().insert_after(Symbol(self, self.grammar))
            rule.last().insert_after(Symbol(self.next, self.grammar))
            
            match.substitute(rule)
            self.substitute(rule)
            
            self.grammar.add_index(rule.first())

        # Check for an under-used rule
        if (rule.first().rule and (rule.first().rule.reference_count == 1)):
            rule.first().expand()
    
    def value(self):
        """docstring for value"""
        return (self.rule.unique_number if self.rule else self.terminal)

    def string_value(self):
        """docstring for string_value"""
        if self.rule:
            return "rule: %d" % self.rule.unique_number
        else:
            return self.terminal

    def hash_value(self):
        """docstring for hash_value"""
        return "%s+%s" % (self.string_value(), self.next.string_value())
