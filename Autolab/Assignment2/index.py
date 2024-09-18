import xml.etree.ElementTree as ET
from datetime import datetime

def log_as_dictionary(log):
    case_dict = {}

    lines = log.split("\n")

    for line in lines:
        # Ignore empty lines
        if line.strip():  # This checks if the line is not empty or just spaces
            elements = line.split(";")
            task_id, case_id, user_id, time_stamp = elements

            event = {
                'task': task_id,
                'user': user_id,
                'time_stamp': time_stamp
            }
            if case_id in case_dict:
                case_dict[case_id].append(event)
            else:
                case_dict[case_id] = [event]

    return case_dict

def dependency_graph_inline(log_dict, transition_name='task'):
    df = {}
    
    for case_id, events_arr in log_dict.items():
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
                if key == 'cost':
                    value = int(value)
                elif key == 'time:timestamp':
                    # Parse the timestamp into a datetime object
                    value = datetime.fromisoformat(value.replace('Z', '+00:00')).replace(tzinfo=None)
                
                event_data[key] = value
            
            events.append(event_data)
        
        if case_id:
            log_data[case_id] = events
    
    return log_data
    
    
def dependency_graph_file(log):
    return dependency_graph_inline(log, transition_name='concept:name')