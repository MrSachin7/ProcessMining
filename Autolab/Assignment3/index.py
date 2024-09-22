import xml.etree.ElementTree as ET
from datetime import datetime, date
import json


class PetriNet():
    def __init__(self):
        self.places = {} # place_id -> no_of_tokens
        self.transitions = {} # transition_id -> {name, input, output}
        
    def add_place(self, place):
        self.places[place] = 0
    
    def add_transition(self, name, id):
        self.transitions[id] = {"name": name, 'input': [], 'output': []}
        
    def transition_name_to_id(self, name):
        for id, transition in self.transitions.items():
            if transition['name'] == name:
                return id
        return None 

        
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
    
    # 4.1 Find the dependency graph
    d_graph = dependency_graph(event_logs)
    
    # 4.2 Find the casual relations
    casual_relations = get_causal_relations(d_graph)
    
    # 4.3 Find the parallel relations
    parallel_relations = get_parallel_relations(d_graph)
    
    # Step4: Final step: All places in casual relations and not in parallel relations
    step4_relations =casual_not_parallel(casual_relations, parallel_relations)
    
    # Step 5 is ignored for now....
    
    # Step 7 , lets generate the Petri Net
    p.add_place('Start')
    p.add_marking('Start') # Add a token to the start place
    p.add_place('End')
    
    
    
    # Push the start and end transitions
    for transition in first_occuring_transitions:
        p.add_transition(transition, transition)
        p.add_edge('Start', transition)
        
    for transition in last_occuring_transitions:
        p.add_transition(transition, transition)
        p.add_edge(transition, 'End')
    
    for relation in step4_relations:
        transition0 = relation[0]
        transition1 = relation[1]
    
        
        place = generate_place(transition0, transition1)       
        
        p.add_place(place)
        
        if transition0 not in first_occuring_transitions:
            p.add_transition(transition0, transition0)
            
        if transition1 not in last_occuring_transitions:
            p.add_transition(transition1, transition1)
        
        p.add_edge(transition0, place)
        p.add_edge(place, transition1)  
    
    return p
    
    

    
    
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

 # Step4.1 : Lets first find the 
def dependency_graph(event_log):
    df = {}
    for case_id, events_arr in event_log.items():
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

# Step4.2 Get casual relations i.e A -> B  and not B -> A
def get_causal_relations(dependency_graph):
    casual_relations = set()
    for step, transitions in dependency_graph.items():
        for transition in transitions:
            if (transition, step) in casual_relations:
                casual_relations.remove((transition, step))
            else:
                casual_relations.add((step, transition))
            
        # TODO : Remember the (A, (B, C)) scenario  
    return casual_relations

# Step4.3 Get parallel relations i.e A -> B  and B -> A
def get_parallel_relations(dependency_graph):
    parallel_relations = set()
    temp = set()
    for step, transitions in dependency_graph.items():
        for transition in transitions:
            if (transition, step) in temp:
                parallel_relations.add((step, transition))
            else:
                temp.add((step, transition))
    return parallel_relations

# Step 4: Final step casual relations and not in parallel relations

def casual_not_parallel(casual_relations, parallel_relations):
    return casual_relations - parallel_relations


def generate_place(t1, t2):
    return t1 + '->' + t2
    

logs = read_from_file('extension-log-3.xes')
d_graph =dependency_graph(logs)
mined_model = alpha(logs)
print("\n")
print ("Step 1: Unique tasks :" , generate_unique_set(logs))
print("\n")
print ("Step 2: First occuring transitions :" , generate_first_occuring_transitions(logs))
print("\n")
print ("Step 3: Last occuring transitions :" , generate_last_occuring_transitions(logs))
print("\n")

print ("Step 4.1: Dependency Graph :" , dependency_graph(logs))
print("\n")

print ("Step 4.2: Casual Relations :" , get_causal_relations(d_graph))
#

print("\n")
print ("Step 4.3: Parallel Relations :" , get_parallel_relations(d_graph))



print("\n")
print("\n")
print("\n")
print("\n")
print("\n")
print("\n")
print("Alpha", mined_model.places)


def check_enabled(pn):
    ts = ["record issue", "inspection", "intervention authorization", "action not required", "work mandate", "no concession", "work completion", "issue completion"]
    for t in ts:
        print (pn.is_enabled(pn.transition_name_to_id(t)))
    print("")
    
trace = ["record issue", "inspection", "intervention authorization", "work mandate", "work completion", "issue completion"]
for a in trace:
    check_enabled(mined_model)
    mined_model.fire_transition(mined_model.transition_name_to_id(a))

    
    
    

