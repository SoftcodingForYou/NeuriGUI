from PyQt5                                  import QtCore, QtWidgets, QtGui
from pyqtgraph                              import PlotWidget
from PIL                                    import Image, ImageTk
from tkinter                                import ttk
from sys                                    import platform
import tkinter                              as tk

class Aux:

    def __init__(self):
        self.img_neuri    = './frontend/Neuri_logo.png'
        self.get_screen_info()


    def get_screen_info(self):
        root = tk.Tk()
        # Get information about screen to center the windows
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        root.destroy()


    def disp_pyqt_splash(self):
        splash_pix = QtGui.QPixmap(self.img_neuri)
        splash_pix = splash_pix.scaled(500, 500, QtCore.Qt.KeepAspectRatio)
        splash = QtWidgets.QSplashScreen(splash_pix, QtCore.Qt.WindowStaysOnTopHint)
        splash.show()

    
    def disp_splash(self):
        root = tk.Tk()

        # multiple image size by zoom
        pixels_x, pixels_y = tuple([int(0.10 * x) for x in Image.open(self.img_neuri).size])
        img = ImageTk.PhotoImage(Image.open(self.img_neuri).resize((pixels_x, pixels_y)), master=root)

        x_cordinate = int((self.screen_width/2) - (pixels_x/2))
        y_cordinate = int((self.screen_height/2) - (pixels_y/2))

        # Only define position, size automatic based on widget sizes,
        # instead of format(pixels_x, round(pixels_y*1.05), x_cordinate, y_cordinate))
        root.geometry("+{}+{}".format(x_cordinate, y_cordinate))
        pb          = ttk.Progressbar(root, orient='horizontal', length=pixels_x, mode='determinate')
        pb.pack()

        if platform == "linux" or platform == "linux2":
            root.overrideredirect(True)
            root.wait_visibility(root)
            root.wm_attributes("-alpha", 0.5)
        elif platform == "darwin":
            root.overrideredirect(True)
            # Make the root window always on top
            root.wm_attributes("-topmost", True)
            # Turn off the window shadow
            root.wm_attributes("-transparent", True)
            # Set the root window background color to a transparent color
            root.config(bg='systemTransparent')
            # Store the PhotoImage to prevent early garbage collection
            root.image = img
            # Display the image on a label
            label = tk.Label(root, image=root.image)
            # Set the label background color to a transparent color
            label.config(bg='systemTransparent')
            label.pack()
        elif platform == "win32":
            root.image = img
            label = tk.Label(root, image=root.image, bg='white')
            root.overrideredirect(True)
            root.lift()
            root.wm_attributes("-topmost", True)
            root.wm_attributes("-disabled", True)
            root.wm_attributes("-transparentcolor", "white")
            label.pack()

        return root, pb
    

    def report_progress(self, target, pb, increment):
        target.attributes('-topmost', True)
        pb.step(increment)
        target.update()