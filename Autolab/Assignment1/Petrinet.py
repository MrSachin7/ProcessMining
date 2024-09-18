class PetriNet():
    def __init__(self):
        self.places = {} # place_id -> no_of_tokens
        self.transitions = {} # transition_id -> {name, input, output}
        
    def add_place(self, place):
        self.places[place] = 0
    
    def add_transition(self, name, id):
        self.transitions[id] = {"name": name, 'input': [], 'output': []}
        
    def add_edge(self, source, target):
        if source in self.places and target in self.transitions:
            self.transitions[target]['input'].append(source)
        elif source in self.transitions and target in self.places:
            self.transitions[source]['output'].append(target)
        return self
        
    def get_tokens(self, place):
        return self.places[place]
    
    def is_enabled(self, transition):
        for place in self.transitions[transition]['input']:
            # if any input place has 0 tokens, return False
            if self.places[place] == 0:
                return False
        return True
    
    def add_marking(self, place):
        self.places[place] += 1
        
    def fire_transition(self, transition):
        if not self.is_enabled(transition):
            print(f"Transition {transition} is not enabled and cannot fire.")
            return
        # subtract tokens from input places and add tokens to output places
        for place in self.transitions[transition]['input']:
            self.places[place] -= 1
        for place in self.transitions[transition]['output']:
            self.places[place] += 1 
            
            
p = PetriNet()
p.add_place(1)  # add place with id 1
p.add_place(2)
p.add_place(3)
p.add_place(4)
p.add_transition("A", -1)  # add transition "A" with id -1
p.add_transition("B", -2)
p.add_transition("C", -3)
p.add_transition("D", -4)

p.add_edge(1, -1)
p.add_edge(-1, 2)
p.add_edge(2, -2).add_edge(-2, 3)
p.add_edge(2, -3).add_edge(-3, 3)
p.add_edge(3, -4)
p.add_edge(-4, 4)

print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.add_marking(1)  # add one token to place id 1
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-1)  # fire transition A
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-3)  # fire transition C
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-4)  # fire transition D
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.add_marking(2)  # add one token to place id 2
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-2)  # fire transition B
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-4)  # fire transition D
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

# by the end of the execution there should be 2 tokens on the final place
print(p.get_tokens(4)) 