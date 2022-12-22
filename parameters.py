#Board unit-specific parameters
HELMENTID       = '7&74D8485&0&24D7EBA4446A_C00000000' # The unique ID of the board (str)

#Session-specific parameters
yrange          = [-600, 600] # List of scalars ([negative, positive]) in order to set figure y axis range

#Signal arrays
sample_rate     = 200 #Hertz
buffer_channels = 2 #scalar
buffer_length   = 10 #scalar (seconds)
buffer_add      = 4 #scalar (seconds), we add this to the buffer for filtering to avoid edge artifacts
sample_count    = 0 #integer zero
saving_interval = 1 #scarlar (seconds)
PGA             = 24 #scalar

#Signal reception
baud_rate       = 115200 #scalar default baudrate for connection
port            = '' #Leave blank as dynamically scanned for later
time_out        = None #Wait for message

#Plotting
plot_intv       = 200 #scalar defining update rate of figure (ms)
s_down          = 5 #Desired downsampling factor (buffer_length*sample_rate/s_down must be convertable to integer)


#Signal processing
filter_order    = 3 #scalar
frequency_bands = {
    'LineNoise':    (46, 54),
    'Whole':        (1, 40)}