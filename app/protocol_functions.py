import numpy.random as random
from netqasm.sdk.classical_communication.message import StructuredMessage


def try_create_epr_pair(connection, epr_socket, socket):
    # success = False
    sender_name = socket.app_name
    receiver_name = socket.remote_app_name
    # while not success:
    print(f"{sender_name} is trying to create an EPR-pair and sending it to {receiver_name}")
    # qubit.measure()
    # connection.flush()

    epr = epr_socket.create()[0]

    connection.flush()
    socket.send_structured(
        StructuredMessage(f"Hey {sender_name}, I tried sending you a qubit, did you receive it? Best, {receiver_name}",
                          True))
    success = socket.recv_structured().payload
    if success:
        print(f"Success! {sender_name} and {receiver_name} have created entanglement")
    else:
        print(f"Failure! {sender_name} and {receiver_name} did not create entanglement and will retry")

        epr.measure()
        connection.flush()

    return epr, success


def try_recv_epr_pair(connection, epr_socket, socket, p_success=0.5):
    # success = False
    sender_name = socket.app_name
    receiver_name = socket.remote_app_name
    # while not success:
    print(f"{sender_name} is waiting to receive an EPR-pair from {receiver_name}")

    epr = epr_socket.recv()[0]

    connection.flush()
    socket.recv_structured()
    success = random.random() <= p_success
    socket.send_structured(StructuredMessage(f"Hey {sender_name}, this is my answer. Best, {receiver_name}", success))
    if not success:
        epr.measure()
        connection.flush()

    return epr, success


def try_entanglement_swap_receive_and_send_measurements_to_next_node(connection, epr1, epr2, socket_in, socket_out,
                                                                     trials,
                                                                     p_success=1.0):
    print(f"{socket_in.app_name} is trying to perform entanglement swapping")
    epr1.cnot(epr2)
    epr1.H()
    b = epr1.measure()
    a = epr2.measure()
    connection.flush()
    print(
        f"{socket_in.app_name} has successfully performed entanglement swapping and awaits data from {socket_in.remote_app_name} before it will send the correction terms to {socket_out.remote_app_name}.")

    b, a = bool(b), bool(a)
    if "repeater_0" not in socket_in.app_name:
        b_0, a_0, trials_0 = socket_in.recv_structured().payload
        b = b_0 ^ b
        a = a_0 ^ a
        trials = max(trials_0,trials)
    connection.flush()
    socket_out.send_structured(StructuredMessage("Corrections and number of trials", (b, a, trials)))
    print(f"{socket_in.app_name} has sent the correction terms to {socket_out.remote_app_name}")
