import os
import numpy as np
from multiprocessing import Pool
from shutil import rmtree, copyfile
from time import time

import json
# The number with which the p_fidelity is increased in network.yaml
delta_fidelity = 0.1

# An empty array to store the output values in



p_fidelity = 0.5
max_number_of_repeater_nodes = 10
number_of_iterations_per_variation =200
number_of_parallel_processes = 8

file_name = f"data_0.5"

def initialize_and_teleport(dummy):
    t_start = time()
    # Run the program without logging, to increase speed and prevent errors
    output = os.popen(f'cd run && netqasm simulate --formalism dm --log-to-files FALSE').read()
    t = time() - t_start
    # output = os.popen('netqasm simulate').read()
    # print(output)
    d = int(output.splitlines()[-1])
    attempts = int(output.splitlines()[-2])
    print(f"{dummy}. Repeaters: {NN+1}, parameter: {p_fidelity}, outcome:{d}, attempts:{attempts}, runtime {t}")
    return d ,t, attempts



for NN in range(0,max_number_of_repeater_nodes):
    number_of_repeater_nodes = NN + 1
    print(number_of_repeater_nodes)
    time_measurements = []
    attempt_measurements = []

    measurements = []

    # Loop over the p_fidelity
    # The starting p_fidelity for the network.yaml file
    p_fidelity = 0.0
    while p_fidelity <=1:
        # fidelity = 0.25

        try:
            rmtree("run")
        except:
            pass
        os.mkdir("run")
        copyfile("protocol_functions.py","run/protocol_functions.py")
        file_template = open("_alice.py", "rt")
        file = open("run/app_alice.py", "x")

        for line in file_template:
            # read replace the string and write to output file
            file.write(
                line.replace("repeater", f"repeater_0"))  # .replace('    fidelity: 1.0', '    fidelity: ' + str(p_fidelity)))
        file_template.close()
        file.close()

        file_template = open("_network.yaml", "rt")
        file = open("run/network.yaml", "w")

        for line in file_template:
            # read replace the string and write to output file
            for ii in range(number_of_repeater_nodes):
                line = line.replace('  - name: "delft"',
                                    f'  - name: "repeater_{ii}"\n    gate_fidelity: 1\n    qubits:\n      - id: 0\n        t1: 0\n        t2: 0\n      - id: 1\n        t1: 0\n        t2: 0\n  - name: "delft"')  # .replace('    fidelity: 1.0', '    fidelity: ' + str(p_fidelity))
            file.write(line)

        for ii in range(number_of_repeater_nodes + 1):
            file.write("\n")
            file.write(f"  - name: ch{ii}")
            file.write("\n")
            if ii == 0:
                file.write(f'    node_name1: "the_hague"')
            else:
                file.write(f'    node_name1: "repeater_{ii - 1}"')
            file.write("\n")
            if ii == number_of_repeater_nodes:
                file.write(f'    node_name2: "delft"')
            else:
                file.write(f'    node_name2: "repeater_{ii}"')
            file.write("\n")
            file.write(f'    noise_type: Depolarise')
            file.write("\n")
            file.write(f'    fidelity: {p_fidelity}')

        file_template.close()
        file.close()

        file_template = open("_roles.yaml", "rt")
        file = open("run/roles.yaml", "w")
        for line in file_template:
            # read replace the string and write to output file
            file.write(line)

        for ii in range(number_of_repeater_nodes):
            file.write("\n")
            file.write(f"repeater_{ii}: 'repeater_{ii}'")

        file_template.close()
        file.close()

        for ii in range(number_of_repeater_nodes):
            file_template = open("_repeater.py", "rt")
            file = open(f"run/app_repeater_{ii}.py", "x")

            for line in file_template:
                # read replace the string and write to output file
                line = line.replace("repeater", f"repeater_{ii}")
                if ii == 0:
                    line = line.replace("node_in", "alice")
                else:
                    line = line.replace("node_in", f"repeater_{ii - 1}")

                if ii == number_of_repeater_nodes - 1:
                    line = line.replace("node_out", "bob")
                else:
                    line = line.replace("node_out", f"repeater_{ii + 1}")

                file.write(line)

            file_template.close()
            file.close()

        file_template = open("_bob.py", "rt")
        file = open("run/app_bob.py", "x")

        for line in file_template:
            # read replace the string and write to output file
            file.write(line.replace("repeater",
                                    f"repeater_{number_of_repeater_nodes - 1}"))  # _{number_of_repeater_nodes-1}"))#.replace('    fidelity: 1.0', '    fidelity: ' + str(p_fidelity)))
        file_template.close()
        file.close()



        fidelity_measurement = []
        for jj in np.arange(0,number_of_iterations_per_variation,number_of_parallel_processes):
            rg = range(jj,jj+number_of_parallel_processes)
            while True:
                try:
                    while True:
                        pool = Pool(processes=number_of_parallel_processes)

                        output = pool.map_async(initialize_and_teleport, rg)
                        output.wait(timeout=240)
                        if output.ready():
                            print("All processes ended in time")
                            output_f, output_time, output_attempts = zip(*output.get(timeout=1))

                            fidelity_measurement.extend(output_f)
                            time_measurements.extend(output_time)
                            attempt_measurements.extend(output_attempts)
                            break
                        else:
                            pool.close()
                            pool.terminate()
                            pool.join()
                            print("Timeout, retry!")
                    break
                except IndexError:
                    print("Retry")
                except ValueError:
                    print("Retry")


        print(p_fidelity,np.mean(time_measurements), np.mean(attempt_measurements), np.mean(fidelity_measurement))

        measurements.append([p_fidelity, np.mean(fidelity_measurement)])
        p_fidelity += delta_fidelity

    # Convert the measurements to an array
    time_measurements = [np.mean(time_measurements), np.std(time_measurements)]
    attempt_measurements = [np.mean(attempt_measurements), np.std(attempt_measurements)]

    time_measurements = np.array(time_measurements)
    attempt_measurements = np.array(attempt_measurements)

    data_list = [number_of_parallel_processes, number_of_iterations_per_variation, max_number_of_repeater_nodes,
                 measurements, [time_measurements.tolist()], [attempt_measurements.tolist()]]

    data_string = json.dumps(data_list)
    file = open(file_name+f"_{number_of_repeater_nodes}.json", "w")
    file.write(data_string)
    file.close()




