from index import *
from json import *

# mined_model = alpha(read_from_file("extension-log-3.xes"))

# def check_enabled(pn):
#   ts = ["record issue", "inspection", "intervention authorization", "action not required", "work mandate", "no concession", "work completion", "issue completion"]
#   for t in ts:
#     print (pn.is_enabled(pn.transition_name_to_id(t)))
#   print("")


# trace = ["record issue", "inspection", "intervention authorization", "work mandate", "work completion", "issue completion"]
# for a in trace:
#   check_enabled(mined_model)
#   mined_model.fire_transition(mined_model.transition_name_to_id(a))

model = alpha(read_from_file("extension-log-3.xes"))

log = read_from_file("extension-log-3.xes")
casual = get_casual_pairs(relation_matrix=relation_matrix(dependency_graph=dependency_graph(log)))
print(dumps(list(casual), indent=4))