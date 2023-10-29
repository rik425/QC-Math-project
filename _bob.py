from netqasm.sdk import EPRSocket
from netqasm.sdk.external import NetQASMConnection, Socket, get_qubit_state
from netqasm.sdk.toolbox.sim_states import qubit_from, to_dm, get_fidelity
from netqasm.sdk.classical_communication.message import StructuredMessage
from protocol_functions import try_recv_epr_pair
def main(app_config=None):

    # Create a socket to recv classical information
    socket = Socket("bob", "alice")
    socket_rep = Socket("bob", "repeater")

    # Create a EPR socket for entanglement generation
    epr_socket = EPRSocket("repeater")

    # Initialize the connection
    bob = NetQASMConnection(
        app_name=app_config.app_name,
        epr_sockets=[epr_socket]
    )
    with bob:
        success = False
        while not success:
            epr, success = try_recv_epr_pair(bob,epr_socket,socket_rep)


        # Get the corrections from the repeater
        m1, m2, trials = socket_rep.recv_structured().payload
        print(f"`bob` got corrections: {m1}, {m2}")
        if m2:
            print("`bob` will perform X correction")
            epr.X()
        if m1:
            print("`bob` will perform Z correction")
            epr.Z()

        socket.send_structured(StructuredMessage("Hey Alice, you can start",True))
        # Get the corrections from Alice
        m1, m2 = socket.recv_structured().payload
        print(f"`bob` got corrections: {m1}, {m2}")
        if m2:
            print("`bob` will perform X correction")
            epr.X()
        if m1:
            print("`bob` will perform Z correction")
            epr.Z()

        bob.flush()
        # Get the qubit state
        # NOTE only possible in simulation, not part of actual application
        dm = get_qubit_state(epr)
        print(f"`bob` recieved the teleported state {dm}")

        # Reconstruct the original qubit to compare with the received one
        # NOTE only to check simulation results, normally the alice does not
        # need to send the phi and theta values!
        msg = socket.recv_silent()  # don't log this
        phi, theta = eval(msg)

        original = qubit_from(phi, theta)
        original_dm = to_dm(original)
        fidelity = get_fidelity(original, dm)**2
        m = epr.measure()
        bob.flush()
        print("Bob received connection after this number of trials and has measured the teleported qubit and found it in state:")
        print(trials)
        print(1-m)
        # print(2/3*(fidelity+0.5))
        # print(fidelity)
        # return {
        #     "original_state": original_dm.tolist(),
        #     "correction1": "Z" if m1 == 1 else "None",
        #     "correction2": "X" if m2 == 1 else "None",
        #     "received_state": dm.tolist(),
        #     "p_fidelity": fidelity
        # }
    return

if __name__ == "__main__":
    main()
