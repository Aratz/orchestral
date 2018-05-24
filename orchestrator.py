import sys
import json
import dask
import string
import functools
import subprocess
from dask.diagnostics import ProgressBar

from distributed import Client

client = Client('localhost:8786')
get = client.get


with open(sys.argv[1], 'r') as f:
    config = json.load(f)

network_file = sys.argv[2]
with open(network_file, 'r') as f:
    network = json.load(f)

TIMEOUT = 60

def run_cell(input_file, output_file, **kwargs):
    for _ in range(3):
        command_line = config["cell_executable"].format(
            input_file=input_file,
            output_file=output_file,
            **kwargs).split()
        proc = subprocess.Popen(command_line)
        try:
            returncode = proc.wait(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            kwargs['seed'] += 1
        else:
            break
    else:
        raise subprocess.TimeoutExpired(command_line, TIMEOUT)
    if returncode:
        raise Exception("GFRD failure")
    return output_file

def run_translation_X2S(input_files, output_file, **kwargs):
    command_line = config["translation_X2S"].format(
        cell_output_files=" ".join(input_files),
        signaling_input_file=output_file,
        **kwargs).split()
    return_code = subprocess.call(command_line)
    return output_file

def run_signaling(input_file, output_file, **kwargs):
    command_line = config["signaling_executable"].format(
        input_file=input_file,
        output_file=output_file,
        **kwargs).split()
    return_code = subprocess.call(command_line)
    return output_file

def run_translation_S2X(target_cell_output_file, signaling_files, output_file, **kwargs):
    command_line = config["translation_S2X"].format(
        target_cell_output_file=target_cell_output_file,
        signaling_files=" ".join(signaling_files),
        target_cell_input_file=output_file,
        **kwargs).split()
    return_code = subprocess.call(command_line)
    return output_file


dag = {}
for step in range(1, config["n_steps"] + 1):
    for cell_id, cell_config in network.items():
        input_file = config["data_folder"] + "/cell-{}-{}.in".format(step, cell_id)
        output_file = config["data_folder"] + "/cell-{}-{}.out".format(step, cell_id)
        dag[output_file] = (
                functools.partial(
                    run_cell,
                    output_file=output_file,
                    **{
                        keyword:network[cell_id][keyword]
                        for keyword in 
                        [keyword for _, keyword, _, _
                            in string.Formatter().parse(config["cell_executable"])
                            if keyword not in ["input_file", "output_file"]]
                        }
                ),
                input_file)

    for cell_id, cell_config in network.items():
        for neighbor_id in cell_config["neighbors"]:
            if neighbor_id < int(cell_id):
                # Avoid duplicate pairs
                continue
            input_files = [
                config["data_folder"] + "/cell-{}-{}.out".format(step, cell_id),
                config["data_folder"] + "/cell-{}-{}.out".format(step, neighbor_id)
                ]
            output_file = config["data_folder"] +  "/signaling-{}-({},{}).in".format(step, cell_id, neighbor_id)

            dag[output_file] = (
                    functools.partial(
                        run_translation_X2S,
                        output_file=output_file,
                        network_file=network_file,
                    ),
                    input_files)


    for cell_id, cell_config in network.items():
        for neighbor_id in cell_config["neighbors"]:
            if neighbor_id < int(cell_id):
                # Avoid duplicate pairs
                continue
            input_file = config["data_folder"] +  "/signaling-{}-({},{}).in".format(step, cell_id, neighbor_id)
            output_file = config["data_folder"] + "/signaling-{}-({},{}).out".format(step, cell_id, neighbor_id)
            dag[output_file] = (
                    functools.partial(
                        run_signaling,
                        output_file=output_file,
                        **{
                            keyword:network[cell_id][keyword]
                            for keyword in 
                            [keyword for _, keyword, _, _
                                in string.Formatter().parse(config["signaling_executable"])
                                if keyword not in ["input_file", "output_file"]]
                            }
                    ),
                    input_file)

    for cell_id, cell_config in network.items():
        input_files = [
            config["data_folder"] + "/signaling-{}-({},{}).out".format(
                step, *sorted([int(cell_id), neighbor_id]))
            for neighbor_id in cell_config["neighbors"]
            ]
        output_file = config["data_folder"] + "/cell-{}-{}.in".format(step + 1, cell_id)
        dag[output_file] = (
                functools.partial(
                    run_translation_S2X,
                    output_file=output_file,
                    network_file=network_file
                    ),
                config["data_folder"] + "/cell-{}-{}.out".format(step, cell_id),
                input_files)

from dask.diagnostics import Profiler

with Profiler() as prof:
    get(dag, [config["data_folder"] + "/cell-{}-{}.out".format(config["n_steps"], cell_id) for cell_id in network], retries=3)

with open(sys.argv[4], 'w') as f:
    json.dump(
            [{
                key: value
                for key, value in task._asdict().items()
                if key in ['key', 'start_time', 'end_time']
                }
                for task in prof.results],
            f)
