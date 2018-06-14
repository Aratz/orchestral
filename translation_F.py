import sys
import json

with open(sys.argv[2]) as f:
    input_data = json.load(f)

with(open sys.argv[3]) as f:
    json.dump(input_data["final"], f)


