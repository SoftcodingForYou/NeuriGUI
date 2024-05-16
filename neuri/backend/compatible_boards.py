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
except: # Necessary if running as Python package
    from .signal_sampling_neuri_v1      import SamplingUtilsNeuriV1Helment
    from .signal_sampling_neuri_lolin   import SamplingUtilsNeuriLolinHelment
    from .signal_sampling_bioamp        import SamplingUtilsBioAmpUpsideDownLabs


COMPATIBLE_BOARDS = {
    # Unique name: [Start code (int, None if no code required), Sampling rate (Hz), baud rate (int), Board_specific class (object)]
    "Neuri V1 by Helment":                  [2, 200, 115200, SamplingUtilsNeuriV1Helment],
    "Neuri-Lolin S3-PRO by Helment":        [2, 200, 115200, SamplingUtilsNeuriLolinHelment],
    "BioAmp EXG Pill by Upside Down Labs":  [2, 125, 115200, SamplingUtilsBioAmpUpsideDownLabs],
}