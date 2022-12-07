#Prepare userland =========================================================
from backend.Helment_configure_board        import ConfigureBoard
from backend.Helment_signal_sampling        import Sampling
from backend.Helment_signal_visualization   import Plotting
from backend.Helment_parameter_validation   import ParamVal
from multiprocessing                        import Process, Pipe


if __name__ == '__main__': # Necessary line for "multiprocessing" to work

    pmval           = ParamVal()            # Sanity checks
    confboard       = ConfigureBoard()      # Board communication
    sigproc         = Sampling()            # Signal handling
    sigplots        = Plotting()            # Visualization
    
    # Listen to user input for setting state of board
    # ---------------------------------------------------------------------
    current_state = -1 # Value that does nothing
    print('Waiting for input: Numerical key stroke...')
    while True:
        current_state = confboard.query_input()
        if current_state == 2 or current_state == 3:
            break

    # Generate variable exchange pipe
    # ---------------------------------------------------------------------
    recv_conn, send_conn = Pipe(duplex = False)

    b = confboard.av_ports

    # Generate separate processes to not slow down sampling by any other
    # executions
    # ---------------------------------------------------------------------
    sampling    = Process(target=sigproc.fetch_sample,
        args=(send_conn, confboard.ser, confboard.av_ports, current_state))
    plotting    = Process(target=sigplots.plot_samples,
        args=(recv_conn,))
    
    if current_state == 2 or current_state == 3:
        sampling.start()
        plotting.start()


    while True:
        if not sampling.is_alive() or not plotting.is_alive():
            print('C key was pressed. Ending script ...')
            sampling.terminate()
            plotting.terminate()
            quit()

