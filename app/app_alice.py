from netqasm.sdk import Qubit, EPRSocket
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk.toolbox import set_qubit_state
# from netqasm.logging.output import get_new_app_logger
from netqasm.sdk.classical_communication.message import StructuredMessage
from protocol_functions import try_create_epr_pair
from promise import Promise

def main(app_config=None, phi=0., theta=0.):
    # log_config = app_config.log_config
    # app_logger = get_new_app_logger(app_name="alice", log_config=log_config)

    # Create a socket to send classical information
    socket = Socket("alice", "bob")#, log_config=log_config)
    socket_rep = Socket("alice", "repeater_0")#, log_config=log_config)


    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("repeater_0")

    print("`alice` will start to teleport a qubit to `bob`")

    # Initialize the connection to the backend
    alice = NetQASMConnection(
        app_name=app_config.app_name,
        # log_config=log_config,
        epr_sockets=[epr_socket]
    )
    with alice:
        # Create a qubit to teleport
        success = False
        while not success:
            epr, success = try_create_epr_pair(alice,epr_socket,socket_rep)

        q = Qubit(alice)
        set_qubit_state(q, phi, theta)

        # Create EPR pairs
        # epr = epr_socket.create()[0]
        alice.flush()
        socket.recv_structured()
        alice.flush()
        # Teleport
        q.cnot(epr)
        q.H()
        m1 = q.measure()
        m2 = epr.measure()

    # Send the correction information
    m1, m2 = bool(m1), bool(m2)

    # app_logger.log(f"m1 = {m1}")
    # app_logger.log(f"m2 = {m2}")
    print(f"`alice` measured the following teleportation corrections: m1 = {m1}, m2 = {m2}")
    print("`alice` will send the corrections to `bob`")

    socket.send_structured(StructuredMessage("Corrections", (m1, m2)))

    socket.send_silent(str((phi, theta)))

    return {
        "m1": m1,
        "m2": m2
    }


if __name__ == "__main__":
    main()
