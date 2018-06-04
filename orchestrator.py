import sys
import json
import dask
import string
import functools
import subprocess
from retrying import retry
from dask.threaded import get
from dask.diagnostics import ProgressBar
import logging

logging.basicConfig(filename='orchestral.log',level=logging.DEBUG)
ProgressBar().register()
TIMEOUT = 60

config_file = sys.argv[1]
with open(config_file, 'r') as f:
    config = json.load(f)

network_file = sys.argv[2]
with open(network_file, 'r') as f:
    network = json.load(f)


@retry(stop_max_attempt_number=3)
def run_cell(input_file, output_file, **kwargs):
    for _ in range(3):
        command_line = config["cell_executable"].format(
            input_file=input_file,
            output_file=output_file,
            **kwargs).split()
        proc = subprocess.Popen(command_line,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            logging.error("command line: {}\n Timeout".format(
                ' '.join(command_line)))
            kwargs['seed'] += 1
        else:
            break
    else:
        raise subprocess.TimeoutExpired(command_line, TIMEOUT)
    if not proc.returncode:
        logging.debug("command line: {}\nreturn code: {}".format(
            ' '.join(command_line), proc.returncode))
    else:
        logging.error("command line: {}\n stdout: {}\n stderr: {}".format(
            ' '.join(command_line), outs, errs))
        raise Exception("GFRD failure")
    return output_file

def run_translation_X2S(input_files, output_file, **kwargs):
    command_line = config["translation_X2S"].format(
        config_file=config_file,
        cell_output_files=" ".join(input_files),
        signaling_input_file=output_file,
        **kwargs).split()
    return_code = subprocess.call(command_line)
    logging.debug("command line: {}\nreturn code: {}".format(
        ' '.join(command_line), return_code))
    return output_file

def run_signaling(input_file, output_file, **kwargs):
    command_line = config["signaling_executable"].format(
        input_file=input_file,
        output_file=output_file,
        **kwargs).split()
    return_code = subprocess.call(command_line)
    logging.debug("command line: {}\nreturn code: {}".format(
        ' '.join(command_line), return_code))
    return output_file

def run_translation_S2X(target_cell_output_file, signaling_files, output_file, **kwargs):
    command_line = config["translation_S2X"].format(
        config_file=config_file,
        target_cell_output_file=target_cell_output_file,
        signaling_files=" ".join(signaling_files),
        target_cell_input_file=output_file,
        **kwargs).split()
    return_code = subprocess.call(command_line)
    logging.debug("command line: {}\nreturn code: {}".format(
        ' '.join(command_line), return_code))
    return output_file


dag = {}
for step in range(1, config["n_steps"] + 1):
    for cell_id, cell_config in network.items():
        input_file = (config["data_folder"] + "/"
                + config["cell_file"].format(step=step, cell_id=cell_id) + ".in")
        output_file = (config["data_folder"] + "/"
                + config["cell_file"].format(step=step, cell_id=cell_id) + ".out")
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
                config["data_folder"] + "/"
                    + config["cell_file"].format(step=step, cell_id=cell_id) + ".out",
                config["data_folder"] + "/"
                    + config["cell_file"].format(step=step, cell_id=neighbor_id) + ".out",
                ]
            output_file = (config["data_folder"] +  "/" +
                config["signaling_file"].format(
                    step=step,
                    cell_id=cell_id,
                    neighbor_id=neighbor_id
                ) + ".in")

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
            input_file = (config["data_folder"] +  "/"
                + config["signaling_file"].format(
                    step=step,
                    cell_id=cell_id,
                    neighbor_id=neighbor_id
                ) + ".in")
            output_file = (config["data_folder"] + "/" +
                config["signaling_file"].format(
                    step=step,
                    cell_id=cell_id,
                    neighbor_id=neighbor_id
                ) + ".out")
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
            config["data_folder"] + "/"
            + config["signaling_file"].format(
                step=step,
                cell_id=min(int(cell_id), neighbor_id),
                neighbor_id=max(int(cell_id), neighbor_id)
            ) + ".out"
            for neighbor_id in cell_config["neighbors"]
            ]
        output_file = (config["data_folder"] + "/"
            + config["cell_file"].format(step=step + 1, cell_id=cell_id) + ".in")
        dag[output_file] = (
                functools.partial(
                    run_translation_S2X,
                    output_file=output_file,
                    network_file=network_file
                    ),
                config["data_folder"] + "/"
                    + config["cell_file"].format(step=step, cell_id=cell_id) + ".out",
                input_files)

get(
    dag,
    [config["data_folder"] + "/" +
        config["cell_file"].format(step=config["n_steps"], cell_id=cell_id) + ".out"
        for cell_id in network]
)
