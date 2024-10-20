from index import *
log = read_from_file("extension-log-4.xes")
log_noisy = read_from_file("extension-log-noisy-4.xes")

mined_model = alpha(log)
print(round(fitness_token_replay(log, mined_model), 5))
print(round(fitness_token_replay(log_noisy, mined_model), 5))