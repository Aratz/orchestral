import sys
import json
import dask
import parse
import string
import argparse
import functools
import subprocess
from dask.diagnostics import ProgressBar

parser = argparse.ArgumentParser(description="Orchestral")
parser.add_argument('-config', help="Config file")
parser.add_argument('-dry-run', help="print commands without executing them",
        action='store_true')

args = vars(parser.parse_args())

TIMEOUT = 60
from distributed import Client

client = Client('localhost:8786')
get = client.get


config_file = args['config']
with open(config_file, 'r') as f:
    config = json.load(f)

def run_mechanics(input_file, output_file, **kwargs):
    command_line = config["mechanics_executable"].format(
            input_file=input_file,
            output_file=output_file,
            **kwargs).split()

    if args['dry_run']:
        print(" ".join(command_line))
        return output_file

    return_code = subprocess.call(command_line)
    if return_code:
        raise Exception("DLCM failure: {}".format(command_line))
    return output_file

def run_cell(input_file, output_file, **kwargs):
    for _ in range(3):
        command_line = config["cell_executable"].format(
            input_file=input_file,
            output_file=output_file,
            **kwargs).split()

        if args['dry_run']:
            print(" ".join(command_line))
            return output_file

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
        raise Exception("GFRD failure: {}".format(command_line))
    return output_file

def run_translation_X2S(input_files, output_file, **kwargs):
    command_line = config["translation_X2S"].format(
        config_file=config_file,
        cell_output_files=" ".join(input_files),
        signaling_input_file=output_file,
        **kwargs).split()

    if args['dry_run']:
        print(" ".join(command_line))
        return output_file

    return_code = subprocess.call(command_line)
    if return_code:
        raise Exception("X2S failure: {}".format(command_line))
    return output_file

def run_signaling(input_file, output_file, **kwargs):
    command_line = config["signaling_executable"].format(
        input_file=input_file,
        output_file=output_file,
        **kwargs).split()

    if args['dry_run']:
        print(" ".join(command_line))
        return output_file

    return_code = subprocess.call(command_line)
    if return_code:
        raise Exception("Signaling failure: {}".format(command_line))
    return output_file

def run_translation_S2X(target_cell_output_file, signaling_files, output_file, **kwargs):
    command_line = config["translation_S2X"].format(
        config_file=config_file,
        target_cell_output_file=target_cell_output_file,
        signaling_files=" ".join(signaling_files),
        target_cell_input_file=output_file,
        **kwargs).split()

    if args['dry_run']:
        print(" ".join(command_line))
        return output_file

    return_code = subprocess.call(command_line)
    if return_code:
        raise Exception("S2X failure: {}".format(command_line))
    return output_file

def generate_network_input(network_output, network_input, **kwargs):
    command_line = config["generate_network_input"].format(
        config_file=config_file,
        network_output=network_output,
        network_input=network_input,
        **kwargs).split()

    if args['dry_run']:
        print(" ".join(command_line))
        return output_file

    return_code = subprocess.call(command_line)
    if return_code:
        raise Exception("network_input failure: {}".format(command_line))
    return network_input

def update_network(network_output):
    command_line = config["update_network"].format(
        config_file=config_file,
        network_output=network_output
        ).split()

    if args['dry_run']:
        print(" ".join(command_line))
        return

    return_code = subprocess.call(command_line)
    if return_code:
        raise Exception("update_network failure: {}".format(command_line))
    return


end_time = config["simulation_time"] / config["n_mech_steps"]
network_file = "{}/{}".format(config["data_folder"],
        config["network_file"].format(step=0) + '.out')
for step in range(config["n_mech_steps"]):
    dag = {}
    sub_end_time = end_time / config["n_kin_substeps"]

    with open(network_file, 'r') as f:
        network = json.load(f)

    for substep in range(config["n_kin_substeps"]):
        for cell_id, cell_config in network["final"].items():
            input_file = (config["data_folder"] + "/"
                    + config["cell_file"].format(step=step, substep=substep, cell_id=cell_id) + ".in")
            output_file = (config["data_folder"] + "/"
                    + config["cell_file"].format(step=step, substep=substep, cell_id=cell_id) + ".out")
            dag[output_file] = (
                    functools.partial(
                        run_cell,
                        output_file=output_file,
                        end_time=sub_end_time,
                        **{
                            keyword:network["final"][cell_id][keyword]
                            for keyword in 
                            [keyword for _, keyword, _, _
                                in string.Formatter().parse(config["cell_executable"])
                                if keyword not in ["input_file", "output_file", "end_time"]]
                            }
                    ),
                    input_file)

        for signal in network["signaling"]:
            input_files = [
                    config["data_folder"] + "/"
                        + config["cell_file"].format(
                            step=step,
                            substep=substep,
                            cell_id=cell_id,
                            ) + ".out"
                        for cell_id in signal]
            output_file = (config["data_folder"] +  "/" +
                config["signaling_file"].format(
                    step=step,
                    substep=substep,
                    signaling_id="{}".format(",".join([signal_id for signal_id in signal])),
                ) + ".in")
            dag[output_file] = (
                    functools.partial(
                        run_translation_X2S,
                        output_file=output_file,
                        network_file=network_file,
                    ),
                    input_files)

        for signal in network["signaling"]:
            input_file = (config["data_folder"] +  "/" +
                config["signaling_file"].format(
                    step=step,
                    substep=substep,
                    signaling_id="{}".format(",".join([signal_id for signal_id in signal])),
                ) + ".in")
            output_file = (config["data_folder"] +  "/" +
                config["signaling_file"].format(
                    step=step,
                    substep=substep,
                    signaling_id="{}".format(",".join([signal_id for signal_id in signal])),
                ) + ".out")
            dag[output_file] = (
                    functools.partial(
                        run_signaling,
                        output_file=output_file,
                        end_time=sub_end_time,
                        seed=network["final"][cell_id]["seed"]+step+substep,
                        **{
                            keyword:network["final"][cell_id][keyword]
                            for keyword in
                            [keyword for _, keyword, _, _
                                in string.Formatter().parse(config["signaling_executable"])
                                if keyword not in ["input_file", "output_file", "end_time", "seed"]]
                            }
                    ),
                    input_file)

        cell2signal = {}
        for signal in network["signaling"]:
            for cell_id in signal:
                if cell_id in cell2signal:
                    cell2signal[cell_id].append(signal)
                else:
                    cell2signal[cell_id] = [signal]

        for cell_id, cell_config in network["final"].items():
            input_files = [
                config["data_folder"] + "/"
                + config["signaling_file"].format(
                    step=step,
                    substep=substep,
                    signaling_id="{}".format(",".join([signal_id for signal_id in signal])),
                ) + ".out"
                for signal in cell2signal.get(cell_id, [])
                ]
            output_file = (config["data_folder"] + "/"
                + config["cell_file"].format(
                    step=step + (substep+1)//config["n_kin_substeps"],
                    substep=(substep + 1) % config["n_kin_substeps"],
                    cell_id=cell_id
                    ) + ".in")
            dag[output_file] = (
                    functools.partial(
                        run_translation_S2X,
                        output_file=output_file,
                        network_file=network_file
                        ),
                    config["data_folder"] + "/"
                        + config["cell_file"].format(
                            step=step,
                            substep=substep,
                            cell_id=cell_id) + ".out",
                    input_files)

    get(
        dag,
        [config["data_folder"] + "/" +
            config["cell_file"].format(
                step=step+1,
                substep=0,
                cell_id=cell_id,
                ) + ".in"
            for cell_id in network["final"]]
    )

    network_file = run_mechanics(
            generate_network_input(
                network_file,
                "{}/{}".format(config["data_folder"],
                    config["network_file"].format(step=step + 1) + ".in")
                ),
            "{}/{}".format(config["data_folder"],
                config["network_file"].format(step=step + 1) + ".out"),
            tstep=step + 1,
            seed=config["seed"] + step,
            end_time=end_time,
            )

    update_network(
            "{}/{}".format(config["data_folder"],
                config["network_file"].format(step=step + 1) + ".out"))
