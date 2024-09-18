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



# Step4.1 : Find appropriate relations between the transitions
def generate_relations(d_graph):
    casual, parallel, choice, loop = set(), set(), set(), set()
    

logs = read_from_file('extension-log-3.xes')
d_graph =dependency_graph(logs)
print("\n")
print ("Step 1: Unique tasks :" , generate_unique_set(logs))
print("\n")
print ("Step 2: First occuring transitions :" , generate_first_occuring_transitions(logs))
print("\n")
print ("Step 3: Last occuring transitions :" , generate_last_occuring_transitions(logs))
print("\n")

print ("Step 4: Dependency Graph :" , dependency_graph(logs))
#

