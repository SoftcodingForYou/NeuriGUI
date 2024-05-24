"""Manual board management
For every board, we collect here the sampling functions and store them 
inside the same class. For this, you need to manage the imports and
dictionnary manually, adding the imported object in fourth position of 
the board's [list].
"""
try:
    from signal_sampling_neuri_v1       import SamplingUtilsNeuriV1Helment
    from signal_sampling_neuri_lolin    import SamplingUtilsNeuriLolinHelment
    from signal_sampling_bioamp         import SamplingUtilsBioAmpUpsideDownLabs
    from signal_sampling_muse_s         import SamplingUtilsMuseSInteraxon
except: # Necessary if running as Python package
    from .signal_sampling_neuri_v1      import SamplingUtilsNeuriV1Helment
    from .signal_sampling_neuri_lolin   import SamplingUtilsNeuriLolinHelment
    from .signal_sampling_bioamp        import SamplingUtilsBioAmpUpsideDownLabs
    from .signal_sampling_muse_s        import SamplingUtilsMuseSInteraxon


# Set None where parameter is not required
COMPATIBLE_BOARDS = {
    # Unique name: [
    #   0: Start code (int or None),
    #   1: Main sampling rate (EEG for most boards) (Hz),
    #   2: Baud rate (int),
    #   3: Board_specific class (object),
    #   4: Number of channels (int),
    #   5: Uses lab streaming layer LSL (bool),
    #   6: Possible to set PGA (bool),
    #   7: Sampling rate of secondary data type applicable, ie PPG (int or None),
    #   8: Amount of channels for secondary data type (ie PPG) (int or None),
    #   9: Default Programmable Gain Amplitude (int or None)
    # ]
    "Neuri V1 by Helment": [
        2,
        200,
        115200,
        SamplingUtilsNeuriV1Helment,
        2,
        False,
        True,
        None,
        None,
        24,
    ],
    "Neuri-Lolin S3-PRO by Helment": [
        2,
        200,
        115200,
        SamplingUtilsNeuriLolinHelment,
        8,
        False,
        True,
        None,
        None,
        24,
    ],
    "BioAmp EXG Pill by Upside Down Labs": [
        None,
        125,
        115200,
        SamplingUtilsBioAmpUpsideDownLabs,
        1,
        False,
        False,
        None,
        None,
        None,
    ],
    "Muse S by InteraXon": [
        None,
        256,
        None,
        SamplingUtilsMuseSInteraxon,
        6,
        True,
        False,
        64,
        3,
        None,
    ]
}