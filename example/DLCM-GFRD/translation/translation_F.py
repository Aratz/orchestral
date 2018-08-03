import sys
import json

with open(sys.argv[2], 'r') as f:
    input_data = json.load(f)

with open(sys.argv[3], 'w') as f:
    json.dump(input_data["final"], f)


