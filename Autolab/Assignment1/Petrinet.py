class PetriNet():
    def __init__(self):
        self.places = {} # place_id -> no_of_tokens
        self.transitions = {} # transition_id -> {name, input, output}
        
    def add_place(self, place):
        if not place in self.places:
            self.places[place] = 0
    
    def add_transition(self, name, id):
        if not id in self.transitions:
            self.transitions[id] = {"name": name, 'input': [], 'output': []}
        
    def transition_name_to_id(self, name):
        for id, transition in self.transitions.items():
            if transition['name'] == name:
                return id
        return None 

        
    def add_edge(self, source, target):
        if source in self.places and target in self.transitions:
            if self.transitions[target]['input'] is None or source not in self.transitions[target]['input']:
             self.transitions[target]['input'].append(source)
        elif source in self.transitions and target in self.places:
            if self.transitions[source]['output'] is None or target not in self.transitions[source]['output']:
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
            
    def to_dict(self):
        """Convert the object into a dictionary for serialization"""
        return {
            "places": self.places,
            "transitions": self.transitions
        }
