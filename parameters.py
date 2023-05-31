#Board unit-specific parameters
# HELMENTID       = '7&2F45FB97&0&C049EF8FE4D2_C00000000' # The unique ID of the board (str)

#Session-specific parameters
yrange          = [-1000, 1000] # List of scalars ([negative, positive]) in order to set figure y axis range
notch           = 0 # Integer 0 (Off), 50 (50 Hz) or 60 (60 Hz)
bpass           = 0 # Integer -1 to 3 according to number of options in "frequency_bands" below
dispenv         = False # Boolean 0 (Off), 1 (On)

#Signal arrays
sample_rate     = 200 #Hertz
buffer_channels = 2 #scalar
buffer_length   = 20 #scalar (seconds)
buffer_add      = 4 #scalar (seconds), we add this to the buffer for filtering to avoid edge artifacts
sample_count    = 0 #integer zero
saving_interval = 1 #scalar (seconds)
PGA             = 24 #scalar

#Signal reception
baud_rate       = 115200 #scalar default baudrate for connection
port            = '' #Leave blank as dynamically scanned for later
time_out        = None #Wait for message

# Signal relay
udp_ip          = "127.0.0.1" # Loopback ip for on-device communication

#Plotting
# plot_intv       = 200 #scalar defining update rate of figure (ms) OBSOLETE PARAMETER
s_down          = 5 #Desired downsampling factor (buffer_length*sample_rate/s_down must be convertable to integer)


#Signal processing
filter_order    = 3 #scalar
frequency_bands = {
    'LineNoise':    (46, 54),
    'LineNoise60':  (56, 64),
    'Sleep':        (1, 30),
    'Theta':        (4, 8),
    'Whole':        (0.5, 45)}