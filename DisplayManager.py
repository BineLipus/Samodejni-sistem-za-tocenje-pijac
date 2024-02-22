import sys
import threading
import time
import traceback
from decimal import Decimal

from GPIOManager import GPIOManager
from LanguageManager import LanguageManager
from tkinter import *

import Drawer
from PIL import Image, ImageTk


class MyFrame(Frame):

    def __init__(self, master=None, cnf=None, **kw):
        super().__init__(master, cnf)
        self.elements = None
        self.setup()

    def setup(self):
        self.elements = dict()  # Dictionary for child elements
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    def getChild(self, element_name):
        return self.elements.get(element_name)

    def getChildren(self) -> dict:
        return self.elements


class MyLabel(Label):

    def __init__(self, master: MyFrame, element_name, **kw):
        super(MyLabel, self).__init__(master, kw)
        self.name = element_name
        self.master = master
        master.elements.setdefault(element_name, self)  # Just add element to a dictionary
        if self.cget("background") is None:
            self.configure(background=master.cget("background"))  # Set same background as used frame

    def get_master(self):
        return self.master


class DisplayManager:
    DISPLAY_BACKLIGHT_TOGGLE_PIN = 29

    selected_beer_count: int = 0  # Used for checking when to return to prompt frame
    active_frame: MyFrame = None
    frame_initialization: MyFrame = None
    frame_selected_beer: MyFrame = None
    frame_error: MyFrame = None
    frame_prompt: MyFrame = None
    frame_pouring: MyFrame = None
    frame_pouring_finished: MyFrame = None
    window = None
    display_running = False
    label = None
    log_label = None
    display_data = dict()
    main_thread = None
    gui_thread = None

    @staticmethod
    def initialize(gui_language):
        LanguageManager.set_language(gui_language)
        GPIOManager.setup(DisplayManager.DISPLAY_BACKLIGHT_TOGGLE_PIN, GPIOManager.OUT)
        DisplayManager.main_thread = threading.Thread(target=DisplayManager.start)
        DisplayManager.main_thread.start()

    @staticmethod
    def terminate():
        DisplayManager.display_running = False
        DisplayManager.gui_thread.join()
        #print("GUI refresh thread joined")
        DisplayManager.window.quit()
        #print("GUI window exited")
        try:
            DisplayManager.main_thread._stop()
        except Exception as e:
            #traceback.print_exception(*sys.exc_info())  # Prints stack trace
            a = 1  # do nothing
        #print("GUI main thread joined")

    @staticmethod
    def start():
        DisplayManager.__setupWindow__()

        # Setup frames
        DisplayManager.__setupInitializationFrame__()
        DisplayManager.__setupPromptFrame__()
        DisplayManager.__setupSelectedBeerFrame__()
        DisplayManager.__setupPouringFinishedFrame__()
        DisplayManager.__setupPouringFrame__()
        DisplayManager.__setupErrorFrame__()

        DisplayManager.display_running = True

        # Start the GUI update function in a separate thread
        DisplayManager.gui_thread = threading.Thread(target=DisplayManager.refreshWindow)
        DisplayManager.gui_thread.start()

        DisplayManager.window.bind('<Control-f>', DisplayManager.toggleFullscreen)

        GPIOManager.output(DisplayManager.DISPLAY_BACKLIGHT_TOGGLE_PIN, GPIOManager.HIGH)
        DisplayManager.window.mainloop()
        print("mainloop broken")

    @staticmethod
    def refreshWindow():
        while DisplayManager.display_running:
            elements = DisplayManager.active_frame.getChildren()
            # TODO: put this in a function and call it using after on window
            # self.root.after(0, self.update_frames_on_main_thread, new_values)
            for child in elements:
                DisplayManager.refreshElement(elements[child], DisplayManager.getDisplayDataValue(child))
            DisplayManager.__showFrame__(DisplayManager.active_frame)
            time.sleep(0.050)  # Refresh screen every 50 ms

    @staticmethod
    def refreshElement(element, value):
        text = None
        if element.name == "remaining_balance_label":
            if value is None:
                element.config(fg=element.get_master().cget("background"))  # Creates invisibility
            else:
                element.config(fg="#000")
        if "." not in element.name and isinstance(value, str):
            text = LanguageManager.get_text_with_parameter(element.name, value)
        elif "." in element.name:
            object = element.name.split(".")[0]
            property = element.name.split(".")[1]
            value = DisplayManager.getDisplayDataValue(object)
            actual_value = None
            if object == "beer":
                if property == "title":
                    actual_value = value.get_name()
                elif property == "style":
                    actual_value = value.get_style()
                elif property == "abv":
                    actual_value = value.get_abv()
                elif property == "image":
                    photo = Drawer.color_beer_image(int(value.get_ebc()))
                    element.config(image=photo)
                    element.image = photo
                    return

                elif property == "ibu":
                    bitterness = min(((value.get_ibu() // 20) + 1), 5)
                    actual_value = str(bitterness) + "/" + str(5)
                elif property == "kcal":
                    actual_value = value.get_kcal()
                elif property == "price":
                    actual_value = value.get_price_per_liter()
            text = LanguageManager.get_text_with_parameter(element.name, str(actual_value))
        element.config(text=text)

    @staticmethod
    def toggleFullscreen(signal):
        if DisplayManager.window.attributes('-fullscreen'):
            DisplayManager.window.attributes('-fullscreen', False)
        else:
            DisplayManager.window.attributes('-fullscreen', True)

    @staticmethod
    def showSelectedBeerFrame():
        DisplayManager.selected_beer_count += 1
        DisplayManager.__showFrame__(DisplayManager.frame_selected_beer)

    @staticmethod
    def decrementSelectedBeerCount():
        if DisplayManager.selected_beer_count > 0:
            DisplayManager.selected_beer_count -= 1

    @staticmethod
    def showErrorFrame():
        DisplayManager.__showFrame__(DisplayManager.frame_error)

    @staticmethod
    def showPouringFrame():
        DisplayManager.__showFrame__(DisplayManager.frame_pouring)

    @staticmethod
    def showPouringFinishedFrame():
        DisplayManager.__showFrame__(DisplayManager.frame_pouring_finished)

    @staticmethod
    def showPromptFrame():
        DisplayManager.__showFrame__(DisplayManager.frame_prompt)

    @staticmethod
    def switchBackToPromptFrame():
        time.sleep(10)
        DisplayManager.decrementSelectedBeerCount()
        if DisplayManager.selected_beer_count == 0 and DisplayManager.active_frame == DisplayManager.frame_selected_beer:
            DisplayManager.showPromptFrame()

    @staticmethod
    def setDisplayData(data: dict):
        DisplayManager.display_data = data

    @staticmethod
    def getDisplayData() -> dict:
        return DisplayManager.display_data

    @staticmethod
    def setDisplayDataValue(key: str, value):
        DisplayManager.display_data[key] = value

    @staticmethod
    def clearDisplayDataValue(key: str):
        if DisplayManager.getDisplayDataValue(key) is not None:
            DisplayManager.display_data.pop(key)

    @staticmethod
    def getDisplayDataValue(key: str):
        if key in DisplayManager.display_data:
            return DisplayManager.display_data[key]
        return None

    @staticmethod
    def __showFrame__(frame):
        if frame != DisplayManager.active_frame:
            # Refresh only on change. Avoid flickering
            if DisplayManager.active_frame is not None:
                DisplayManager.active_frame.pack_forget()  # Unload the frame
            frame.pack(expand=True, fill=BOTH)  # Loads the new frame
            DisplayManager.window.update_idletasks()  # Updates the whole display (cascades through GUI objects and displays them)
            DisplayManager.active_frame = frame

    @staticmethod
    def __setupWindow__():
        DisplayManager.window = Tk()
        DisplayManager.window.title("BeerTapMachine")
        DisplayManager.window.attributes('-fullscreen', True)
        DisplayManager.window.config(cursor="none")  # Hides the cursor
        DisplayManager.window.rowconfigure(0, weight=1)
        DisplayManager.window.columnconfigure(0, weight=1)

    @staticmethod
    def __setupInitializationFrame__():
        DisplayManager.frame_initialization = MyFrame(DisplayManager.window)
        DisplayManager.frame_initialization.grid_rowconfigure(0, weight=5)
        DisplayManager.frame_initialization.grid_rowconfigure(1, weight=1)
        DisplayManager.frame_initialization.grid_rowconfigure(2, weight=1)
        DisplayManager.frame_initialization.grid_rowconfigure(3, weight=5)

        # Create and style the labels
        Label(DisplayManager.frame_initialization,
              text=LanguageManager.get_text("welcome_label"),
              font=("Arial", 36, "bold"),
              justify="center",
              wraplength=700) \
            .grid(column=0, row=1, pady=(50, 10))

        Label(DisplayManager.frame_initialization,
              text=LanguageManager.get_text("info_label"),
              font=("Arial", 30),
              justify="center",
              wraplength=700) \
            .grid(column=0, row=2, pady=(100, 10))

        DisplayManager.__showFrame__(DisplayManager.frame_initialization)

    @staticmethod
    def __setupErrorFrame__():
        DisplayManager.frame_error = MyFrame()
        DisplayManager.frame_error.grid_rowconfigure(0, weight=2)
        DisplayManager.frame_error.grid_rowconfigure(1, weight=1)

        MyLabel(DisplayManager.frame_error, "error_label",
                text=LanguageManager.get_text("error_label"),
                font=("Arial", 30),
                justify="center",
                wraplength=700) \
            .grid(column=0, row=0)

        MyLabel(DisplayManager.frame_error, "remaining_balance_label",
                text=LanguageManager.get_text("remaining_balance_label"),
                font=("Arial", 30),
                justify="center",
                wraplength=700) \
            .grid(column=0, row=1)

    @staticmethod
    def __setupPouringFrame__():
        DisplayManager.frame_pouring = MyFrame()

        Label(DisplayManager.frame_pouring,
              text=LanguageManager.get_text("pouring_label"),
              font=("Arial", 30),
              justify="center",
              wraplength=700) \
            .grid(column=0, row=0)

    @staticmethod
    def __setupPouringFinishedFrame__():
        DisplayManager.frame_pouring_finished = MyFrame()

        DisplayManager.frame_pouring_finished.grid_rowconfigure(0, weight=2)
        DisplayManager.frame_pouring_finished.grid_rowconfigure(1, weight=1)

        MyLabel(DisplayManager.frame_pouring_finished, "pouring_finished_label",
                text=LanguageManager.get_text("pouring_finished_label"),
                font=("Arial", 30),
                justify="center",
                wraplength=700) \
            .grid(column=0, row=0)

        MyLabel(DisplayManager.frame_pouring_finished, "remaining_balance_label",
                text=LanguageManager.get_text("remaining_balance_label"),
                font=("Arial", 30),
                justify="center",
                wraplength=700) \
            .grid(column=0, row=1)

    @staticmethod
    def __setupPromptFrame__():
        DisplayManager.frame_prompt = MyFrame()

        Label(DisplayManager.frame_prompt,
              text=LanguageManager.get_text("prompt_label"),
              font=("Arial", 30),
              justify="center",
              wraplength=700) \
            .grid(column=0, row=0)

    @staticmethod
    def __setupSelectedBeerFrame__():
        DisplayManager.frame_selected_beer = MyFrame()
        DisplayManager.frame_selected_beer.grid_columnconfigure(0, weight=1)
        DisplayManager.frame_selected_beer.grid_columnconfigure(1, weight=1)
        DisplayManager.frame_selected_beer.grid_rowconfigure(0, weight=1)
        DisplayManager.frame_selected_beer.grid_rowconfigure(1, weight=1)
        DisplayManager.frame_selected_beer.grid_rowconfigure(2, weight=1)
        DisplayManager.frame_selected_beer.grid_rowconfigure(3, weight=1)
        DisplayManager.frame_selected_beer.grid_rowconfigure(4, weight=1)
        DisplayManager.frame_selected_beer.grid_rowconfigure(5, weight=1)
        DisplayManager.frame_selected_beer.grid_rowconfigure(6, weight=1)
        #DisplayManager.frame_selected_beer.grid_rowconfigure(7, weight=1)

        image = Image.open("beer.png")
        photo = ImageTk.PhotoImage(image)

        photoLabel = MyLabel(DisplayManager.frame_selected_beer, "beer.image",
                             image=photo,
                             width=(DisplayManager.window.winfo_screenwidth() / 2))
        photoLabel.image = photo
        photoLabel.grid(column=1, row=0, rowspan=7)

        MyLabel(DisplayManager.frame_selected_beer, "beer.title",
                text="",
                font=("Arial", 30),
                justify="center") \
            .grid(column=0, row=1)

        MyLabel(DisplayManager.frame_selected_beer, "beer.style",
                text="",
                font=("Arial", 30),
                justify="center") \
            .grid(column=0, row=2)

        MyLabel(DisplayManager.frame_selected_beer, "beer.abv",
                text="",
                font=("Arial", 30),
                justify="center") \
            .grid(column=0, row=3)
        #
        # MyLabel(DisplayManager.frame_selected_beer, "beer.ebc",
        #         text="Beer Color",
        #         font=("Arial", 30),
        #         justify="center") \
        #     .grid(column=0, row=4)

        MyLabel(DisplayManager.frame_selected_beer, "beer.ibu",
                text="",
                font=("Arial", 30),
                justify="center") \
            .grid(column=0, row=4)

        MyLabel(DisplayManager.frame_selected_beer, "beer.kcal",
                text="",
                font=("Arial", 30),
                justify="center") \
            .grid(column=0, row=5)

        MyLabel(DisplayManager.frame_selected_beer, "beer.price",
                text="",
                font=("Arial", 30),
                justify="center") \
            .grid(column=0, row=6)

    @staticmethod
    def get_color_from_ebc(ebc: Decimal):
        # These values are on SRM scale, which is EBC divided by 2.
        colors = ["#FFE699",
                  "#FFD878",
                  "#FFCA5A",
                  "#FFBF42",
                  "#FBB123",
                  "#F8A600",
                  "#F39C00",
                  "#EA8F00",
                  "#E58500",
                  "#DE7C00",
                  "#D77200",
                  "#CF6900",
                  "#CB6200",
                  "#C35900",
                  "#BB5100",
                  "#B54C00",
                  "#B04500",
                  "#A63E00",
                  "#A13700",
                  "#9B3200",
                  "#952D00",
                  "#8E2900",
                  "#882300",
                  "#821E00",
                  "#7B1A00",
                  "#771900",
                  "#701400",
                  "#6A0E00",
                  "#660D00",
                  "#5E0B00",
                  "#5A0A02",
                  "#560905",
                  "#520907",
                  "#4C0505",
                  "#470606",
                  "#440607",
                  "#3F0708",
                  "#3B0607",
                  "#3A070B",
                  "#36080A"]

        color_index = int(ebc // 2)

        return colors[min(len(colors) - 1, max(color_index, 0))]
