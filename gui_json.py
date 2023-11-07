import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import subprocess
import argparse
import shutil
import time

# Create the argument parser
parser = argparse.ArgumentParser(
    description='Search for images within a date range and write metadata to a JSON file.')
parser.add_argument('--file_path', required=True,
                    help='Path to the directory to search for image files.')


# Parse the arguments
args = parser.parse_args()

file_path = args.file_path


# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))

class JsonEditor:

    def __init__(self, master, file_path):
        self.record_keys = []
        self.file_path = file_path
        self.record_status = None
        self.button_frame = None
        self.frame = tk.Frame(master)  # Initialize a frame

        self.master = master
        self.master.title("Image Cataloger")

        # self.image_grid_window = None
        self.current_page = 0
        self.photo_images = []

        # Initialize the image_widgets list
        self.image_widgets = []

        self.tooltip = None

        # create TreeView widget
        self.tree = ttk.Treeview(self.master, columns=(
            "value"), selectmode="extended")
        self.tree.pack(side="left", fill="y", expand=True)
        # set width of Treeview widget

        self.tree.heading("#0", text="Key", anchor="w")
        self.tree.heading("#1", text="Value", anchor="w")
        # increase width of Value column
        self.tree.column("value", minwidth=200)

        # set width of Value column
        self.tree.column("#1", minwidth=0, width=400, stretch=True)

        # create scrollbar
        self.scrollbar = tk.Scrollbar(
            self.master, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=self.scrollbar.set)

        # read JSON file and populate TreeView
        with open(self.file_path, encoding='utf-8') as f:
            self.json_data = json.load(f)
        self.populate_tree(self.json_data, "")

        self.image_path_data = self.extract_image_paths_from_json(
            self.json_data)

        # Create the image grid window instance
        # self.create_image_grid_window(image_path_data, self.json_data)

        # create menu bar
        self.menu_bar = tk.Menu(self.master)
        self.master.config(menu=self.menu_bar)

        # create file menu
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.open_file)
        self.file_menu.add_command(
            label="Run Image Analytics", command=self.run_image_analytics)
        self.file_menu.add_command(
            label="Create a New Catalog", command=self.create_new_catalog)
        self.file_menu.add_command(
            label="Update Existing Catalog", command=self.update_existing_catalog)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.master.quit)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)

        # create view menu
        self.view_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.view_menu.add_command(label="Refresh", command=self.refresh)
        self.view_menu.add_command(
            label="Sort by Date", command=self.sort_by_date)  # New menu item
        self.view_menu.add_command(
            label="Picture Deck", command=lambda: self.show_image_grid(self.image_path_data))

        self.menu_bar.add_cascade(label="View", menu=self.view_menu)

        # bind double-click event to Treeview object
        self.tree.bind("<ButtonRelease-1>", lambda event: self.click_handler(event,
                       self.tree.item(self.tree.focus())))

        # print("image_path_data=", self.image_path_data)

    # extract file paths from json for picture deck

    def extract_image_paths_from_json(self, json_data):
        image_path_data = []
        for _, image_list in json_data.items():
            for image_info in image_list:
                source = image_info.get("source")
                if source:
                    image_path_data.append(source)
        return (image_path_data)

    def show_full_image(self, image_path):
        full_image = Image.open(image_path)

        # Get the screen width and height
        screen_width = self.master.winfo_screenwidth()
        screen_height = self.master.winfo_screenheight()

        # Calculate the desired width and height for the image window (half the screen size)
        window_width = screen_width // 2
        window_height = screen_height // 2

        # Resize the image to fit the window
        full_image.thumbnail((window_width, window_height))

        # Create a new window to display the full-size image
        full_image_window = tk.Toplevel(self.master)
        full_image_window.title(image_path)

        full_photo = ImageTk.PhotoImage(full_image)
        full_label = tk.Label(full_image_window, image=full_photo)
        full_label.image = full_photo
        full_label.pack()

        # Create a frame for buttons at the bottom
        button_frame = tk.Frame(full_image_window)
        button_frame.pack(side=tk.BOTTOM, pady=10)

        # Create a "Cancel" button to close the full-size image window
        cancel_button = tk.Button(
            button_frame, text="Cancel", command=full_image_window.destroy)
        cancel_button.pack(side=tk.LEFT, padx=10)

        # Create a "Properties" button and pass the image_path to the show_image_properties function
        properties_button = tk.Button(
            button_frame, text="Properties", command=lambda path=image_path: self.show_image_properties(path))
        properties_button.pack(side=tk.RIGHT, padx=10)

        # Close the full-size image window when it's double-clicked
        full_label.bind("<Double-Button-1>",
                        lambda e: full_image_window.destroy())

    def show_image_properties(self, image_path):
        # Find the image_info dictionary with the matching "source" key

        self.record_status = None
        image_info = None

        for _, image_list in self.json_data.items():
            for info in image_list:
                if info.get("source") == image_path:
                    image_info = info
                    break

        # Replace "if image_info:" with this code
        if image_info:
            # Convert the image_info to a JSON string
            input_json = json.dumps(image_info, indent=4)

            # Call the input_dialog function to display image properties
            j = self.input_dialog(image_path, input_json)

            if self.record_status == "cancelled":
                return

            if j:
                parent_key = next(iter(self.json_data))

                self.update_json_file(
                    parent_key, j)
                messagebox.showinfo(
                    "Image Properties", "Image data updated")

        else:
            tk.messagebox.showerror(
                "Image Not Found", "Image properties not found in JSON data.")

    def create_image_grid(self, image_path_data, frame, current_page=0):

        num_cols = 5
        start_idx = current_page * 25
        end_idx = start_idx + 25

        for idx, image_path in enumerate(image_path_data[start_idx:end_idx]):
            if os.path.exists(image_path):
                image = Image.open(image_path)
                image.thumbnail((100, 100))
                photo = ImageTk.PhotoImage(image)

                label = tk.Label(frame, image=photo)
                label.image = photo
                label.grid(row=idx // num_cols, column=idx %
                           num_cols, padx=5, pady=5)

                label.bind("<Enter>", lambda e,
                           name=image_path: self.show_tooltip(name))
                label.bind("<Leave>", self.hide_tooltip)

                label.bind("<Double-Button-1>", lambda e,
                           path=image_path: self.show_full_image(path))

                self.image_widgets.append(label)

        button_frame = tk.Frame(frame)
        button_frame.grid(row=idx // num_cols + 1,
                          columnspan=num_cols, pady=10)

        first_25_button = tk.Button(
            button_frame, text="|<<", command=self.show_first_25)
        first_25_button.pack(side=tk.LEFT, padx=10)

        prev_25_button = tk.Button(
            button_frame, text="<", command=self.show_previous_25)
        prev_25_button.pack(side=tk.LEFT, padx=10)

        next_25_button = tk.Button(
            button_frame, text=">", command=self.show_next_25)
        next_25_button.pack(side=tk.LEFT, padx=10)

        last_25_button = tk.Button(
            button_frame, text=">>|", command=self.show_last_25)
        last_25_button.pack(side=tk.LEFT, padx=10)

    def show_image_grid(self, image_path_data):
        self.image_grid_window = tk.Toplevel(self.master)
        self.image_grid_window.title("Image Grid")

        self.create_image_grid(
            image_path_data, self.image_grid_window, self.current_page)
        self.update_title()

    # Add the navigation button methods here

    def update_image_grid(self):

        # Clear only the existing image widgets
        for widget in self.image_grid_window.winfo_children():
            widget.destroy()
        self.image_widgets = []

        # Call the create_image_grid method with the updated data
        self.create_image_grid(self.image_path_data,
                               self.image_grid_window, self.current_page)

    def show_tooltip(self, text):
        self.tooltip_label = tk.Label(
            self.image_grid_window, text=text, background='lightyellow', relief='solid')
        self.tooltip_label.place(relx=0.5, rely=0.5, anchor='center')

    def hide_tooltip(self, event):
        if hasattr(self, 'tooltip_label'):
            self.tooltip_label.destroy()

    def update_title(self):
        total_images = len(self.image_path_data)
        start_range = self.current_page * 25 + 1
        end_range = min((self.current_page + 1) * 25, total_images)
        self.image_grid_window.title(
            f"Image Grid - {start_range} thru {end_range} of {total_images} images")

    def show_first_25(self):
        self.current_page = 0
        self.update_image_grid()

        self.update_title()

    def show_last_25(self):
        num_pages = (len(self.image_path_data) - 1) // 25
        self.current_page = num_pages
        self.update_image_grid()
        self.update_title()

    def show_previous_25(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_image_grid()
            self.update_title()

    def show_next_25(self):
        num_pages = (len(self.image_path_data) - 1) // 25
        if self.current_page < num_pages:
            self.current_page += 1
            self.update_image_grid()
            self.update_title()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if file_path:
            self.file_path = file_path
            self.tree.delete(*self.tree.get_children())
            with open(self.file_path, encoding='utf-8') as f:
                self.json_data = json.load(f)
            self.populate_tree(self.json_data, "")

    def run_image_analytics(self):
        # Construct the relative file path
        self.master.title("Image Cataloger - running image analytics...")
        script_path = os.path.join(script_dir, "image_analytics.py")
        subprocess.Popen(["python", script_path])
        self.master.title("Image Cataloger")

    def create_new_catalog(self):
        # Create a top-level window
        window = tk.Toplevel(self.master)

        # Set the window title
        window.title("Create New Catalog")

        # Create a label and entry widget for each input field
        fields = ["Start Year", "End Year",
                  "Catalog Path", "Search Path", "Ignore File"]

        entry_widgets = []

        for field in fields:
            label = tk.Label(window, text=field)
            label.pack()

            entry = tk.Entry(window)
            entry.pack()

            entry_widgets.append(entry)

        # Create a button to submit the input values
        submit_button = tk.Button(
            window, text="Submit", command=lambda: self.submit_values(window, entry_widgets))
        submit_button.pack()

    def submit_values(self, window, entry_widgets):
        # Get the values from the entry widgets
        values = [entry.get() for entry in entry_widgets]

        # Extract the values for each input field
        start_year, end_year, catalog_path, search_path, ignore_file = values

        # Run the second script using subprocess.Popen
        # Construct the relative file path
        script_path = os.path.join(script_dir, "new_image_catalog_by_year.py")
        subprocess.Popen(["python", script_path, "--start_year", str(start_year), "--end_year", str(end_year),
                         "--catalog_path", catalog_path, "--search_path", search_path, "--ignore_file", ignore_file])

        # Close the input window
        window.destroy()

    def update_existing_catalog(self):
        file_path = filedialog.askopenfilename(
            defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        default_search_path = os.path.expanduser("~")
        default_ignore_file = os.path.join(script_dir, "ignore_this.txt")
        print("file_path=", file_path)
        print("default_ignore_file=", default_ignore_file)

        if file_path:
            # Update the status message
            # messagebox.showinfo("Updating Catalog", "Refreshing catalog, with new items")
            self.master.title(
                "Image Cataloger - updating existing image catalog...")

            # Run the subprocess
            script_path = os.path.join(script_dir, "update_json_by_year.py")
            subprocess.run(["python", script_path, "--catalog_file_path", file_path,
                           "--search_path", default_search_path, "--ignore_file", default_ignore_file])

            # Display the message box
            messagebox.showinfo("Catalog Updated",
                                f"Image catalog refreshed\nFile: {file_path}")
            self.master.title("Image Cataloger")
        else:
            # Update the status message if no file was selected
            self.status_label.config(text="No file selected.")

    def populate_tree(self, node, parent):
        if isinstance(node, dict):

            for key, value in node.items():
                if isinstance(value, (dict, list)):
                    item = self.tree.insert(parent, "end", text=key)
                    self.populate_tree(value, item)
                    self.image_path_data = self.extract_image_paths_from_json(
                        self.json_data)

                else:
                    item = self.tree.insert(
                        parent, "end", text=key, values=(value,))
                    if key in ['artist', 'title', 'media', 'category', 'description', 'year_of_work', 'for_sale', 'price']:
                        # enable editing for the specified keys
                        self.tree.item(item, tags=())
        elif isinstance(node, list):
            for i, item in enumerate(node):
                if isinstance(item, (dict, list)):
                    self.populate_tree(item, parent)
                    # add space between records, except for the last record
                    if i != len(node) - 1:
                        self.tree.insert(parent, "end", text="")
                    self.image_path_data = self.extract_image_paths_from_json(
                        self.json_data)
                else:
                    self.tree.insert(parent, "end", text="", values=(item,))
                    # add space between records, except for the last record
                    if i != len(node) - 1:
                        self.tree.insert(parent, "end", text="")

    def build_dictionary(self, start_item_id, n):
        record = {}
        item_id = start_item_id

        for i in range(n):
            item_values = self.tree.item(item_id)
            if item_values:
                key = item_values['text']
                values = item_values['values']
                record[key] = values

            item_id = self.tree.next(item_id)
            if not item_id:
                break

        # converts dictionary to json string
        json_str = json.dumps(record)

        return json_str

    def click_handler(self, event, item):
        self.record_status = "ok"
        if event.num == 1:

            if 'source' in item['text']:
                start_item_id = self.tree.focus()
                path = item['values'][0]

                if os.path.exists(path):
                    values = self.build_dictionary(start_item_id, 13)

                    parent_key = self.get_parent_value(
                        start_item_id)  # catalog name also top of json

                    # open the image
                    image = Image.open(path)
                    # resize the image to fit the window
                    width, height = image.size
                    new_width = min(width, 800)
                    new_height = int(height * (new_width / width))
                    image = image.resize((new_width, new_height))
                    photo = ImageTk.PhotoImage(image)
                    # display the image in a label widget
                    label = tk.Label(root, image=photo)
                    # keep a reference to the photo to prevent it from being garbage collected
                    label.image = photo
                    label.pack()
                    title = path

                    j = self.input_dialog(title, values)
                    label.destroy()  # destroy the label widget to clear the image

                    # need the following to convert lists to JSON dictionary 20231106
                    for key in j:
                        if len(j[key]) == 1:
                            j[key] = j[key][0]

                    if self.record_status == "cancelled":
                        return

                    if j:
                        self.update_json_file(parent_key, j)
                        messagebox.showinfo(
                            "Image Properties", "Image data updated")

                else:
                    messagebox.showerror(
                        "Image not found", "The image file does not exist.")

    def get_parent_value(self, start_item_id):
        parent_item_value = self.tree.item(self.tree.parent(start_item_id))
        parent_key = parent_item_value['text']

        if parent_key:
            return parent_key
        else:
            return None

    # input_dialog
    def input_dialog(self, title, key_value):
        input_list = [(k, v) for k, v in json.loads(key_value).items()]

        # Create a tkinter window
        window = tk.Toplevel()
        window.title(title)
        # Set the window size
        fixed_size = (500, 400)
        window.geometry(f"{fixed_size[0]}x{fixed_size[1]}")
        window.minsize(fixed_size[0], fixed_size[1])
        window.maxsize(fixed_size[0], fixed_size[1])

        entry_list = []
        input_values = {}

        for _, (key, value) in enumerate(input_list):
            frame = tk.Frame(window)
            label = tk.Label(frame, text=key, anchor="w")
            label.pack(side=tk.LEFT)
            entry_value = str(value).strip("{'[]'}")

            if key in ["source", "device_id", "load_date", "date_modified"]:
                entry = tk.Entry(frame, width=50)
                entry.insert(0, entry_value)
                entry.config(state="readonly")
            elif key in ["category"]:
                # Modify the values as needed
                combobox = ttk.Combobox(
                    frame, values=["Work", "Personal", "Other"])
                combobox.set(entry_value)  # Set the default value
                entry = combobox
            elif key in ["media"]:
                # Modify the values as needed                combobox.set(value)  # Set the default value
                combobox = ttk.Combobox(
                    frame, values=["Digital Art","Digital Photo","Other", "Scanned Document"])
                combobox.set(entry_value)
                entry = combobox
            else:
                entry = tk.Entry(frame, width=50)
                entry.insert(0, entry_value)

            entry.pack(side=tk.LEFT, fill="x", expand=True)
            frame.pack(fill="x", expand=True)
            entry_list.append(entry)
            input_values[key] = value

        # Define a function to get the input values
        def get_input():
            for i, (key, value) in enumerate(input_list):
                if key not in ["source", "device_id", "load_date", "date_modified"]:
                    input_values[key] = entry_list[i].get()
            # Add the "timestamp" field with the current timestamp
            input_values["timestamp"] = str(int(time.time()))
            window.destroy()

        def flip_image():
            image = Image.open(title)
            flipped_image = image.rotate(180)
            flipped_image.show()

        # Define a function to rotate the image left by 90 degrees
        def rotate_image_left():
            image = Image.open(title)
            rotated_image = image.rotate(-90)
            rotated_image.show()

        # Define a function to rotate the image right by 90 degrees
        def rotate_image_right():
            image = Image.open(title)
            rotated_image = image.rotate(90)
            rotated_image.show()

        # Define a function to move the selected file to the trash folder
        def move_to_trash():
            get_input()
            catalog_dir = os.path.dirname(os.path.abspath(__file__))
            # Create the trash directory if it doesn't exist
            trash_dir = os.path.join(catalog_dir, 'trash')
            if not os.path.exists(trash_dir):
                os.mkdir(trash_dir)
            # Move the file to the trash directory
            shutil.move(title, trash_dir)
            # Print a message
            self.record_status = "moved"
            messagebox.showinfo("Moved to Trash", title)

        # Create a function to handle the Cancel button click

        def cancel_input():
            self.record_status = "cancelled"
            window.destroy()

        # Create a function to handle the window close event
        def on_window_close():
            self.record_status = "cancelled"
            window.destroy()

        # Set the window close protocol to trigger the on_window_close function
        window.protocol("WM_DELETE_WINDOW", on_window_close)

        # Create a menu bar
        menu_bar = tk.Menu(window)

        # Create a "File" menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Exit", command=window.destroy)

        # Create an "Edit" menu
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        edit_menu.add_command(label="Send to Trash", command=move_to_trash)

        # Create a "View" menu
        view_menu = tk.Menu(menu_bar, tearoff=0)
        view_menu.add_command(label="Flip Image", command=flip_image)
        view_menu.add_command(label="Rotate Image Left 90",
                              command=rotate_image_left)
        view_menu.add_command(label="Rotate Image Right 90",
                              command=rotate_image_right)

        # Add the menus to the menu bar
        menu_bar.add_cascade(label="File", menu=file_menu)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        menu_bar.add_cascade(label="View", menu=view_menu)

        # Add the menu bar to the window
        window.config(menu=menu_bar)

        # Create a button frame to hold the buttons
        button_frame = tk.Frame(window)
        button_frame.pack(pady=10)

        # Create a button to cancel and close the window
        # Add a Cancel button to the input_dialog window
        cancel_button = tk.Button(
            button_frame, text="Cancel", command=cancel_input)
        cancel_button.pack(side="left", padx=5)

        # Create a button to save the input values
        save_button = tk.Button(button_frame, text="Save", command=get_input)
        save_button.pack(side="right", padx=5)

        # Make the window modal
        window.grab_set()
        window.focus_set()
        # This will block the execution of other code until the window is closed.
        window.wait_window()

        # Return the input values
        return input_values

    def update_json_file(self, parent_key, j):

        # Set the last_modified timestamp for the modified dictionary
        j['timestamp'] = int(time.time())
        detail_list = self.json_data[parent_key]

        if self.record_status == "moved":
            # Remove the item from the detail list if record_status is "moved"
            detail_list = [
                item for item in detail_list if item["source"] != j["source"]]
        else:
            for i, item in enumerate(detail_list):
                if os.path.normpath(str(item["source"])) == os.path.normpath(str(j["source"])):
                    detail_list[i] = j
                    break

        self.json_data[parent_key] = detail_list

        # sort list
        sorted_json_data = self.timestamp_sort(self.json_data)

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(sorted_json_data, f, indent=4, ensure_ascii=False)

        self.record_status = None

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        with open(self.file_path, encoding='utf-8') as f:
            self.json_data = json.load(f)
            self.populate_tree(self.json_data, "")

    def timestamp_sort(self, json_data):

        for parent_key, child_dict in json_data.items():
            sorted_dicts = sorted(child_dict, key=lambda x: x.get(
                'timestamp', 0), reverse=True)
            json_data[parent_key] = sorted_dicts
        return json_data

    def sort_by_date(self):
        # Sort the JSON data by the "date_modified" field
        for parent_key, child_dict in self.json_data.items():
            sorted_dicts = sorted(child_dict, key=lambda x: x.get(
                'date_modified', 0), reverse=True)
            self.json_data[parent_key] = sorted_dicts

        # Clear and repopulate the TreeView with the sorted data
        self.tree.delete(*self.tree.get_children())
        self.populate_tree(self.json_data, "")


class Tranport:
    global parent_key


if __name__ == "__main__":
    root = tk.Tk()
    json_editor = JsonEditor(root, file_path)
    root.mainloop()

# end of script
