from netqasm.sdk import Qubit, EPRSocket
from netqasm.sdk.external import NetQASMConnection, Socket
from netqasm.sdk.toolbox import set_qubit_state
from netqasm.logging.output import get_new_app_logger
from netqasm.sdk.classical_communication.message import StructuredMessage
from protocol_functions import try_create_epr_pair, try_recv_epr_pair, try_entanglement_swap_receive_and_send_measurements_to_next_node

def main(app_config=None, phi=0., theta=0.):
    # log_config = app_config.log_config
    # app_logger = get_new_app_logger(app_name="alice", log_config=log_config)

    # Create a socket to send classical information
    socket_A = Socket("repeater_5", "repeater_4")
    socket_B = Socket("repeater_5", "repeater_6")

    # Create a EPR socket for entanglement generation
    epr_socket_A = EPRSocket("repeater_4")
    epr_socket_B = EPRSocket("repeater_6")


    # Initialize the connection to the backend
    repeater_5 = NetQASMConnection(
        app_name=app_config.app_name,
        # log_config=log_config,
        epr_sockets=[epr_socket_A,epr_socket_B]
    )
    with repeater_5:

        # Create EPR pairs
        # epr_A = epr_socket_A.recv()[0]
        success_A = False
        success_B = False
        trials = 0
        while not success_A or not success_B:
            trials +=1
            if not success_A:
                epr_A, success_A = try_recv_epr_pair(repeater_5,epr_socket_A,socket_A)

            if not success_B:
                epr_B, success_B = try_create_epr_pair(repeater_5,epr_socket_B,socket_B)

        # Once both epr pairs have been established, repeater_5 will perform the entanglement swap operation
        try_entanglement_swap_receive_and_send_measurements_to_next_node(repeater_5,epr_A,epr_B,socket_A,socket_B,trials)

    return


if __name__ == "__main__":
    main()
