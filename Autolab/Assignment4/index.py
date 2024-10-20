import xml.etree.ElementTree as ET
from datetime import datetime, date
from collections import defaultdict
from json import *

class PetriNet():
    def __init__(self):
        self.places = {} # place_id -> no_of_tokens
        self.transitions = {} # transition_id -> {name, input, output}
        self.missing = 0
        self.consumed = 0 #Placeholder for the end place
        self.produced = 0 
        
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
            if self.get_tokens(place) == 0:
                return False
        return True
    
    def add_marking(self, place):
        self.places[place] += 1
        self.produced += 1

    def remove_marking(self, place):
        self.places[place] -= 1
        self.consumed += 1
        
    def fire_transition(self, transition, forced = False):
        if transition not in self.transitions:
            raise ValueError(f"Transition {transition} does not exist.")
        
        if not forced and not self.is_enabled(transition):
            print(f"Transition {transition} is not enabled and cannot fire.")
            return
        
        # If the transition is forced
        if forced and not self.is_enabled(transition):
            for place in self.transitions[transition]['input']:
                if self.get_tokens(place) == 0:
                    # Add a token to the place and update the missing token
                    self.places[place] = 1
                    self.missing += 1
            # Here, we guarentee that the transition is enabled
            self.fire_transition(transition, forced=False)

        # subtract tokens from input places and add tokens to output places
        for place in self.transitions[transition]['input']:
            self.remove_marking(place)
            # self.consumed += 1
        for place in self.transitions[transition]['output']:
            self.add_marking(place)
            # self.produced += 1
            
    def to_dict(self):
        #Convert the object into a dictionary for serialization
        return {
            "places": self.places,
            "transitions": self.transitions
        }
    
    def get_current_number_of_tokens(self):
        # End place is not included in the sum
        sum = 0
        for place in self.places:
            if place != 'end':
                sum += self.places[place] 

        return sum
    
    def reset(self):
        self.missing = 0
        self.consumed = 0
        self.remaining = 0
        self.produced = 0
        for place in self.places:
            self.places[place] = 0
        self.add_marking('start')

def read_from_file(filename):
    log_data = {}
    
    # Parse the XES file
    tree = ET.parse(filename)
    root = tree.getroot()
    
    ns = {'xes': 'http://www.xes-standard.org/'}  # Update based on the file if needed
    
    # Loop through each trace (representing a case) in the XES file
    for trace in root.findall('xes:trace', ns):
        case_id = None
        events = []
        
        # Get the trace's case ID (usually in a concept:name attribute)
        for attr in trace.findall('xes:string', ns):
            if attr.attrib['key'] == 'concept:name':
                case_id = attr.attrib['value']
        
        # Loop through each event in the trace
        for event in trace.findall('xes:event', ns):
            event_data = {}
            
            # Extract attributes from the event
            for attr in event:
                key = attr.attrib['key']
                value = attr.attrib['value']
                
                # Parse the value based on the type of the attribute key
                if key == 'cost' or key == 'urgency':
                    value = int(value)
                elif key == 'time:timestamp':
                    # Parse the timestamp into a datetime object
                    value = datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
                
                elif key == 'intervention':
                    value = bool(value)
                
                event_data[key] = value
            
            events.append(event_data)
        
        if case_id:
            log_data[case_id] = events
    
    return log_data


transition_name = 'concept:name'

def alpha(event_logs):
    p = PetriNet()
    
    # Lets consider concept:name as the transition name
    
    # Step 1: Find all unique tasks
    tasks = generate_unique_set(event_logs)
    
    # Step2: Find the first occuring transitions
    first_occuring_transitions = generate_first_occuring_transitions(event_logs)
    
    # Step3: Find all the last occuring transitions
    last_occuring_transitions = generate_last_occuring_transitions(event_logs)
    
    # Step4
    
    #  Find the dependency graph
    d_graph = dependency_graph(event_logs)
    
    # Find the relation matrix
    r_matrix = relation_matrix(d_graph)
    
    
    # Step4 and step5: Final step: All places in casual relations and not in parallel relations
    casusal_relations = get_casual_pairs(r_matrix)
    
    # Add input and output places to the petri net
    p.add_place('start')
    
    # Init start with 1 token
    p.add_marking('start')
    p.add_place('end')
    
    
    for item in first_occuring_transitions:
        p.add_transition(item, item)
        p.add_edge('start', item)
    
    for item in last_occuring_transitions:
        p.add_transition(item, item)
        p.add_edge(item, 'end')
    
    for item1, item2 in casusal_relations:
        # None are tuple
        if not isinstance(item1, tuple) and not isinstance(item2, tuple):
            place = place_name(item1, item2)
            p.add_place(place)
            p.add_transition(item1, item1)
            p.add_edge(source=item1, target=place)
            
            p.add_transition(item2, item2)
            p.add_edge(source=place, target=item2)
        
        # Both are tuple
        elif isinstance(item1, tuple) and isinstance(item2, tuple):
            place = place_name(item1, item2)
            p.add_place(place)
            for i in item1:
                p.add_transition(i, i)
                p.add_edge(source=i, target=place)
            for i in item2:
                p.add_transition(i, i)
                p.add_edge(source=place, target=i)      
                
        elif isinstance(item1, tuple):
            place = place_name(item1, item2)
            p.add_place(place)
            for i in item1:
                p.add_transition(i, i)
                p.add_edge(source=i, target=place)
            p.add_transition(item2, item2)
            p.add_edge(source=place, target=item2)      
        
        elif isinstance(item2, tuple):
            place = place_name(item1, item2)
            p.add_place(place)
            
            p.add_transition(item1, item1)
            p.add_edge(source=item1, target=place)
            
            for i in item2:
                p.add_transition(i, i)
                p.add_edge(source=place, target=i)

    return p


def place_name(t0, t1):
    return f"{t0} -> {t1}"    
        
    
# Step: 1
def generate_unique_set(event_logs):
    tasks = set()
    for _, events in event_logs.items():
        for event in events:
            tasks.add(event[transition_name])
    return tasks


# Step:2 : 
def generate_first_occuring_transitions(event_logs):    
    first_occuring_transitions = set()
    for _, events in event_logs.items():
        first_occuring_transitions.add(events[0][transition_name])
    
    return first_occuring_transitions
        
# Step3:
def generate_last_occuring_transitions(event_logs):
    last_occuring_transitions = set()
    for _, events in event_logs.items():
        last_occuring_transitions.add(events[-1][transition_name])
    
    return last_occuring_transitions

 # Step4.1 : Lets first find the dependency graph
def dependency_graph(event_log):
    df = {}
    for _, events_arr in event_log.items():
        for i in range(len(events_arr)-1):
            event = events_arr[i]
            next_event = events_arr[i+1]
            task = event[transition_name]
            next_task = next_event[transition_name]
            
            if task not in df:
                df[task] = {}
            if next_task not in df[task]:
                df[task][next_task] = 1
            else:
                df[task][next_task] = df[task][next_task] + 1
    return df


def relation_matrix(dependency_graph):
    all_direct_relations = set()
    
    # Collect all direct relations from the dependency graph
    for step, transitions in dependency_graph.items():
        for transition in transitions:
            all_direct_relations.add((step, transition))
    
    # Initialize the matrix with all relations being 'choice'
    matrix = {}
    for t1, t2 in all_direct_relations:
        # Initialize dictionaries if they do not exist
        if t1 not in matrix:
            matrix[t1] = {}
        if t2 not in matrix:
            matrix[t2] = {}
    
        for t1_, t2_ in all_direct_relations:
            # Init with choice
            matrix[t1][t1_] = matrix[t1][t2_] = matrix[t2][t1_] = matrix[t2][t2_] = 'choice'
    
    # Set 'direct', 'reverse', and 'parallel' relations based on conditions
    for t1, t2 in all_direct_relations:
        if matrix[t2][t1] == 'direct':
            matrix[t1][t2] = matrix[t2][t1] = 'parallel'
        else:
            matrix[t1][t2] = 'direct'
            matrix[t2][t1] = 'reverse'
    
    return matrix



# Step 4: Find pairs that are in direct relation and not in parallel to itself:
def get_casual_pairs(relation_matrix):
    result = []
    
    for B in relation_matrix:
        # Collect potential "C" and "D" for simplification
        for C in relation_matrix[B]:
            # Check if B has a direct relation to C, and both B and C have "choice" self-relations
            if (relation_matrix[B][C] == 'direct' and
                relation_matrix[B][B] == 'choice' and
                relation_matrix[C][C] == 'choice'):
                result.append((B, C))
         
    possible_multiple_pairs = []
    
    for item1, item2 in result:
        for item1_, item2_ in result:
            # Skip when the same pair is compared
            if item1 == item1_ and item2 == item2_:
                continue
            
            if item1 == item1_:
                if (relation_matrix[item1][item1] == 'choice' and
                    relation_matrix[item2][item2] == 'choice' and
                    relation_matrix[item2_][item2_] == 'choice' and
                    relation_matrix[item2][item2_] == 'choice'):
                    if ((item1, (item2_, item2)) not in possible_multiple_pairs):
                        possible_multiple_pairs.append((item1, (item2, item2_)))
                    
            if item2 == item2_:
                if(relation_matrix[item2][item2] == 'choice' and
                   relation_matrix[item1][item1] == 'choice' and
                   relation_matrix[item1_][item1_] == 'choice' and
                   relation_matrix[item1][item1_] == 'choice'):
                    if (((item1_, item1), item2) not in possible_multiple_pairs):
                        possible_multiple_pairs.append(((item1, item1_), item2))
    
    # At this point we have all possible multiple pairs
    # Lets remove the redundant pairs
    copy = set(possible_multiple_pairs.copy())
        
    for item1, item2 in possible_multiple_pairs:
        for item1_, item2_ in possible_multiple_pairs:
            if item1 == item1_ and item2 == item2_:
                continue
                
            if item2 == item2_: 
                    # Both not being tuple
                if not isinstance(item1, tuple) and not isinstance(item1_, tuple):
                    if not (item1, item2) in copy or not (item1_, item2_) in copy: continue
                    copy.remove((item1, item2))
                    copy.remove((item1_, item2_))
                    copy.add(((item1, item1_), item2))
                    
                    # Both being tuple
                elif isinstance(item1, tuple) and isinstance(item1_, tuple):
                    if not (item1, item2) in copy or not (item1_, item2_) in copy: continue
                    copy.remove((item1_, item2_))
                    tempSet = set()
                        
                    for i in item1:
                        tempSet.add(i)
                    for i in item1_:
                        tempSet.add(i)
                    tempList = list(tempSet)
                    
                    copy.add((tuple(tempList), item2))
                        
                elif isinstance(item1, tuple) and not isinstance(item1_, tuple):
                    if not (item1, item2) in copy or not (item1_, item2_) in copy: continue
                    copy.remove((item1, item2))
                    copy.remove((item1_, item2_))
                    tempSet = set()
                        
                    for i in item1:
                        tempSet.add(i)
                    tempSet.add(item1_)
                    tempList = list(tempSet)
                    copy.add((tuple(tempList), item2))
                        
                elif not isinstance(item1, tuple) and isinstance(item1_, tuple):
                    if not (item1, item2) in copy or not (item1_, item2_) in copy: continue
                    copy.remove((item1, item2))
                    copy.remove((item1_, item2_))
                    tempSet = set()
                        
                    for i in item1_:
                        tempSet.add(i)
                    tempSet.add(item1)
                    tempList = list(tempSet)
                    copy.add((tuple(tempList), item2))
    
    
    resultCopy = set(result.copy())
    
    for item1, item2 in result:
        for item1_, item2_ in copy:
            if item1 == item1_ and item2 == item2_:
                continue
            if item1 == item1_ or item2 == item2_:
                if (item1, item2) not in resultCopy: continue
                resultCopy.remove((item1, item2))
                resultCopy.add((item1_, item2_))

            

    return resultCopy

"""
Returns a list of unique traces in the log, along with the number of times each trace occurs.
The last element of each trace is the count of the number of times the trace occurs in the log.
"""
def all_traces_with_counts(data):
    trace_counts = defaultdict(int)
    
    # Iterate over each case in the dataset
    for _, events in data.items():
        trace = tuple(event['concept:name'] for event in events)
        trace_counts[trace] += 1

    # Convert the trace dictionary to a list of traces with counts
    result = [list(trace) + [count] for trace, count in trace_counts.items()]
    
    return result



def fitness_token_replay(log, model):
    traces = all_traces_with_counts(log)
    sumNiMi = 0
    sumNiCi = 0
    sumNiRi = 0
    sumNiPi = 0
    for trace in traces:
        Ni = trace[-1]
        trace = trace[:-1]
        (Ci, Pi, Mi, Ri)= fire_transition_in_trace(trace, model)
        sumNiMi += Ni * Mi
        sumNiCi += Ni * Ci
        sumNiRi += Ni * Ri
        sumNiPi += Ni * Pi

        print(", ".join(trace))
        print(f"Consumed: {Ci}, Produced: {Pi}, Missing: {Mi}, Remaining: {Ri}")

        print("\n\n")
        # For the next trace, reset the model
        model.reset()


    f = 0.5 * (1 - (sumNiMi / sumNiCi)) + 0.5 * (1 - (sumNiRi / sumNiPi))
    return f




def fire_transition_in_trace(trace, model):
    for transition in trace:
        model.fire_transition(transition, forced=False)
    return (model.consumed, model.produced, model.missing, model.get_current_number_of_tokens())

model = alpha(read_from_file("extension-log-4.xes"))
print(dumps(model.to_dict(), indent=4))






