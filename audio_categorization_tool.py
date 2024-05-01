import tkinter as tk
import pygame
import glob
import os
from pydub import AudioSegment
import pyaudio
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import threading
import numpy as np
import pandas as pd
import tkinter.filedialog as fd
import tkinter.messagebox as msgbox
import sys


class AudioPlayerGUI:
    def __init__(self, master):
        self.master = master
        self.coding_complete = False  # Initialize as False
        master.title("Audio Categorization Tool")
        master.geometry("600x400")

        # Attempt to load the last used directory
        self.load_last_directory()

        # Always show a folder selection dialog, starting from the last directory if available
        self.request_folder_path()

        if not self.file_directory:
            master.quit()  # Close the application if no folder is selected
        else:
            self.initialize_program()  # Initialize the rest of the program if a folder is selected


        # if not self.file_directory:
        #     self.request_folder_path()  # Request folder path if not loaded
        # else:
        #     self.initialize_program()  # Initialize the rest of the program


        pygame.init()
        pygame.mixer.pre_init(44100, 16, 2, 4096)
        pygame.mixer.init()

        # Waveform plot setup
        # self.figure = plt.Figure(figsize=(5, 2), dpi=100)
        # self.ax = self.figure.add_subplot(111)
        # self.canvas = FigureCanvasTkAgg(self.figure, master)
        # self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)



        self.responses = []
        # self.file_directory = '/Users/leek13/data/deBarbaroCry/P06'
        self.file_list = sorted(glob.glob(os.path.join(self.file_directory, '*.wav')))
        self.current_file_index = 0
        self.selection_made = False

        # Existing initialization code...
        self.folder_name = os.path.basename(self.file_directory)
        # pickle_folder = os.path.join(self.file_directory, ".pickle")  # Define the folder path for pickle files
        pickle_folder = ".pickle"
        # Check if the .pickle directory exists, if not, create it
        if not os.path.exists(pickle_folder):
            os.makedirs(pickle_folder)

        # Check if the results directory exists, if not, create it
        results_dir = 'results'
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        # state_folder = os.path.join(self.file_directory, ".state")  # Define the folder path for state files
        state_folder = 'bookmark'
        # Ensure the .state directory exists, if not, create it
        if not os.path.exists(state_folder):
            os.makedirs(state_folder)
        self.state_file_path = os.path.join(state_folder, f"state-{self.folder_name}.txt")  # Updated state file path

        # Update the path for the dataframe pickle file to be within the .pickle directory
        self.dataframe_path = os.path.join(pickle_folder, f'{self.folder_name}.pickle')
        self.results_path = f'results/{self.folder_name}.csv'

        self.coder_name_label = tk.Label(master, text="Coder Name:")
        self.coder_name_label.pack()

        self.coder_name_entry = tk.Entry(master)
        self.coder_name_entry.pack()

        self.filename_label = tk.Label(master, text="Filename:")
        self.filename_label.pack()

        self.filename_entry = tk.Entry(master)
        self.filename_entry.pack()
        self.update_filename()  # Update initially without depending on load_state

        # Load or initialize dataframe
        if os.path.exists(self.dataframe_path):
            self.df = pd.read_pickle(self.dataframe_path)
        else:
            self.df = pd.DataFrame({
                'coder': [None] * len(self.file_list),
                'folder_name': [self.folder_name] * len(self.file_list),
                'file_idx': list(range(len(self.file_list))),
                'filename': [os.path.basename(f) for f in self.file_list],
                'coding_result': [None] * len(self.file_list)
            })

        self.update_filename()  # To update title with folder name


        self.play_button = tk.Button(master, text="Play", command=self.play_audio)
        self.play_button.pack()

        self.category_var = tk.StringVar(value="")
        categories = ["Cry (1) 😢", "Scream (2) 😱", "Whine/Fuss (3) 😫", "Yelling (4) 😮", "None (5) 🚫", "Not Sure (6) 🤔"]
        self.check_buttons = {}
        for category in categories:
            cb = tk.Checkbutton(master, text=category, variable=self.category_var, onvalue=category, offvalue="None",
                                command=self.enable_next_button)
            cb.pack(anchor=tk.W)
            self.check_buttons[category] = cb

        self.prev_button = tk.Button(master, text="<- Previous", command=self.prev_file)
        self.prev_button.pack(side=tk.LEFT)
        self.prev_button.config(state=tk.DISABLED)

        self.next_button = tk.Button(master, text="Next ->", command=self.next_file)
        self.next_button.pack(side=tk.RIGHT)
        self.next_button.config(state=tk.DISABLED)

        self.skip_button = tk.Button(master, text="Skip to", command=self.skip_to)
        self.skip_button.pack()
        self.load_responses()
        master.protocol("WM_DELETE_WINDOW", self.on_exit)


        # Call load_state after all widgets are created
        self.load_coder_name()
        self.load_state()

        # Initialize the waveform display window and canvas
        self.waveform_window = None
        self.waveform_canvas = None
        self.waveform_figure = None
        self.waveform_ax = None
        self.show_waveform_popup()


        # Add these attributes for audio playback control
        self.playback_thread = None
        # Add these attributes for audio playback control
        self.stream = None
        self.p = None
        self.playing = threading.Event()

    def request_folder_path(self):
        # Directly invoke the folder selection dialog using the last used directory
        initial_dir = self.last_directory if self.last_directory else '/'
        folder_selected = fd.askdirectory(initialdir="/Users/leek13/Downloads/1942", parent=self.master, title="Select Folder")
        if folder_selected:
            self.file_directory = folder_selected
            # self.save_last_directory()  # Save the selected directory
            self.initialize_program()  # Initialize the rest of the program

    def select_folder(self, popup):
        # Use the last directory if available, otherwise default to the root directory
        initial_dir = self.last_directory if self.last_directory else '/'
        folder_selected = fd.askdirectory(initialdir=initial_dir)
        if folder_selected:
            self.file_directory = folder_selected
            # self.save_last_directory()  # Save the selected directory
            popup.destroy()  # Close the popup
            self.initialize_program()  # Initialize the rest of the program


    # def play_audio(self):
    #     filename = self.file_list[self.current_file_index]
    #     pygame.mixer.music.load(filename)
    #     pygame.mixer.music.play()

    def request_folder_path(self):
        # Create a popup window for folder selection
        popup = tk.Toplevel(self.master)
        popup.title("Select Folder")
        popup.geometry("300x100")
        tk.Label(popup, text="Please select the input folder:").pack(pady=10)
        btn_select = tk.Button(popup, text="Browse", command=lambda: self.select_folder(popup))
        btn_select.pack()

        self.master.wait_window(popup)  # Wait for the popup to close before continuing

    def select_folder(self, popup):
        folder_selected = fd.askdirectory()
        if folder_selected:
            self.file_directory = folder_selected
            # self.save_last_directory()  # Save the selected directory
            popup.destroy()  # Close the popup
            self.initialize_program()  # Initialize the rest of the program

    def initialize_program(self):
        self.folder_name = os.path.basename(self.file_directory)
        self.file_list = sorted(glob.glob(os.path.join(self.file_directory, '*.wav')))
        self.current_file_index = 0

        # Load or initialize DataFrame
        self.setup_dataframe()

        # Check if coding is already complete and handle accordingly
        if self.check_if_coding_complete():
            self.show_custom_dialog()  # Show dialog and exit if coding is complete
        else:
            self.setup_gui()  # Setup GUI components if coding is not complete

    def show_custom_dialog(self):
        # Create a popup window for the completion message
        popup = tk.Toplevel(self.master)
        popup.title("Coding Completed")
        message = ("Coding is already completed. If you want to look into coding again, "
                   f"please delete bookmark/{self.folder_name}.txt and restart the program.")
        tk.Label(popup, text=message, wraplength=350, justify="left").pack(pady=10)
        quit_btn = tk.Button(popup, text="Quit", command=self.quit_application)
        quit_btn.pack(pady=20)
        popup.protocol("WM_DELETE_WINDOW", self.quit_application)  # Handle window close action properly

    def quit_application(self):
        """ Cleanly quit the application """
        self.master.quit()  # Quit the main loop
        self.master.destroy()  # Destroy all widgets
        sys.exit()  # Exit the application

    def check_if_coding_complete(self):
        try:
            with open(self.state_file_path, 'r') as f:
                lines = f.readlines()
                if lines and lines[1].strip() == 'done':
                    return True
        except Exception as e:
            print(f"Error reading state file: {e}")
        return False

    def setup_gui(self):
        # Control Buttons
        # self.play_button = tk.Button(self.master, text="Play", command=self.play_audio)
        # self.play_button.pack()

        # Protocol for when the main window is closed
        self.master.protocol("WM_DELETE_WINDOW", self.on_exit)

    def save_last_directory(self):
        with open('last_directory.txt', 'w') as f:
            f.write(self.file_directory)

    def load_last_directory(self):
        try:
            with open('last_directory.txt', 'r') as f:
                last_dir = f.read().strip()
                if os.path.exists(last_dir):
                    self.last_directory = last_dir
        except FileNotFoundError:
            self.last_directory = None

    def setup_dataframe(self):
        pickle_folder = os.path.join(self.file_directory, ".pickle")
        os.makedirs(pickle_folder, exist_ok=True)
        self.dataframe_path = os.path.join(pickle_folder, f'{self.folder_name}.pickle')
        if os.path.exists(self.dataframe_path):
            self.df = pd.read_pickle(self.dataframe_path)
        else:
            self.df = pd.DataFrame({
                'coder': [None] * len(self.file_list),
                'folder_name': [self.folder_name] * len(self.file_list),
                'file_idx': list(range(len(self.file_list))),
                'filename': [os.path.basename(f) for f in self.file_list],
                'coding_result': [None] * len(self.file_list)
            })

    def show_waveform_popup(self):
        if not self.waveform_window:
            self.waveform_window = tk.Toplevel(self.master)
            self.waveform_window.title("Waveform Display")
            self.waveform_window.geometry("400x200")

            self.waveform_figure = plt.Figure(figsize=(4, 2), dpi=100)
            self.waveform_ax = self.waveform_figure.add_subplot(111)

            self.waveform_canvas = FigureCanvasTkAgg(self.waveform_figure, self.waveform_window)
            self.waveform_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.update_waveform()

    def update_waveform(self):
        filename = self.file_list[self.current_file_index]
        data, rate = self.load_waveform_data(filename)

        self.waveform_ax.clear()  # Clear the existing plot
        self.waveform_ax.plot(np.linspace(0, len(data) / rate, num=len(data)), data)
        self.waveform_ax.set_title('Waveform')
        self.waveform_ax.set_xlabel('Time (s)')
        self.waveform_ax.set_ylabel('Amplitude')

        self.waveform_canvas.draw()
    def load_waveform_data(self, filename):
        # Load audio file using soundfile to handle reading different formats and extraction of data
        import soundfile as sf
        data, rate = sf.read(filename, dtype='float32')  # Read data as float32 to normalize amplitude
        return data, rate
    def skip_to(self):
        def confirm():
            index = int(entry.get()) - 1  # Converts input to zero-based index
            if 0 <= index < len(self.file_list):
                self.current_file_index = index
                self.update_filename()
                self.reset_selection()
                window.destroy()

        window = tk.Toplevel(self.master)
        window.title("Skip to File")
        tk.Label(window, text=f"Enter file number index (1-{len(self.file_list)}):").pack()
        entry = tk.Entry(window)
        entry.pack()
        confirm_button = tk.Button(window, text="Confirm", command=confirm)
        confirm_button.pack()

    # def play_audio(self):
    #     import sounddevice as sd
    #     import soundfile as sf
    #     filename = self.file_list[self.current_file_index]
    #     data, fs = sf.read(filename)  # Read the file
    #     sd.play(data, fs)  # Play the audio
    #     self.plot_waveform(data, fs)
    #     sd.wait()  # Wait until the audio is finished playing

    def play_audio(self):
        if self.playing.is_set():
            self.stop_audio()  # Stop any currently playing audio
        else:
            self.playing.set()
            self.play_button.config(text="Playing", state=tk.DISABLED)
            self.next_button.config(state=tk.DISABLED)  # Disable the next button during playback
            self.prev_button.config(state=tk.DISABLED)
            self.skip_button.config(state=tk.DISABLED)  # Disable the skip button during playback
            self.playback_thread = threading.Thread(target=self.playback_audio, daemon=True)
            self.playback_thread.start()

    def stop_audio(self):
        if self.playing.is_set():
            self.playing.clear()
            self.play_button.config(text="Play", state=tk.NORMAL)
            self.prev_button.config(state=tk.NORMAL)  # Re-enable the next button when stopped
            self.next_button.config(state=tk.NORMAL)  # Re-enable the next button when stopped
            self.skip_button.config(state=tk.NORMAL)  # Re-enable the skip button when stopped
            if self.stream is not None:
                try:
                    self.stream.stop_stream()
                except Exception as e:
                    print(f"An error occurred while stopping the stream: {e}")
            self.playback_thread = None

    def playback_audio(self):
        try:
            self.p = pyaudio.PyAudio()
            filename = self.file_list[self.current_file_index]
            audio = AudioSegment.from_wav(filename)
            audio = audio.set_frame_rate(44100).set_sample_width(2)

            self.stream = self.p.open(format=self.p.get_format_from_width(audio.sample_width),
                                      channels=audio.channels,
                                      rate=audio.frame_rate,
                                      output=True)

            # Play the audio in chunks
            chunk_length = 1024  # This is a more common chunk size for PyAudio
            chunk_data = audio.raw_data  # Get all the raw data from the audio segment
            total_chunks = len(chunk_data) // chunk_length

            for i in range(total_chunks + 1):
                if not self.playing.is_set():
                    break  # Stop playing if the event is cleared
                chunk = chunk_data[i * chunk_length:(i + 1) * chunk_length]
                self.stream.write(chunk)

        except Exception as e:
            print(f"An exception occurred during playback: {e}")
        finally:
            # Regardless of whether an exception occurred, clean up
            if self.stream is not None:
                self.stream.stop_stream()
                self.stream.close()
            if self.p is not None:
                self.p.terminate()
            self.stream = None
            self.playing.clear()
            self.play_button.config(text="Play", state=tk.NORMAL)
            # Re-enable the next button only if a selection has been made
            if self.selection_made:
                self.next_button.config(state=tk.NORMAL)
                self.prev_button.config(state=tk.NORMAL)
                self.skip_button.config(state=tk.NORMAL)
            else:
                self.next_button.config(state=tk.DISABLED)
                self.prev_button.config(state=tk.DISABLED)

    # from pydub.playback import play
    #
    # def play_audio(self):
    #     filename = self.file_list[self.current_file_index]
    #     audio = AudioSegment.from_wav(filename)
    #     play(audio)
    #     self.plot_waveform_from_file(filename)

    # def plot_waveform(self, data, fs):
    #     self.ax.clear()  # Clear previous waveform
    #     self.ax.plot(data)
    #     self.ax.set_title('Waveform')
    #     self.ax.set_xlabel('Sample Index')
    #     self.ax.set_ylabel('Amplitude')
    #     self.canvas.draw()  # Redraw the waveform plot

    # def plot_waveform_from_file(self, filename):
    #     import soundfile as sf
    #     data, fs = sf.read(filename)
    #     self.plot_waveform(data, fs)
    def enable_next_button(self):
        self.selection_made = True
        # Enable the next button only if audio is not currently playing
        if not self.playing.is_set():
            self.next_button.config(state=tk.NORMAL)
            self.prev_button.config(state=tk.NORMAL)
        else:
            self.next_button.config(state=tk.DISABLED)
            self.prev_button.config(state=tk.DISABLED)

    def prev_file(self):
        if self.current_file_index > 0:
            self.current_file_index -= 1
            self.update_filename()
            self.reset_selection()

    def next_file(self):
        if self.playing.is_set():
            self.stop_audio()  # Stop any currently playing audio
        if self.current_file_index < len(self.file_list) - 1 and self.selection_made:
            self.save_response()
            self.current_file_index += 1
            self.update_filename()  # Refresh filename and window title
            self.update_waveform()  # Update the waveform display
            self.reset_selection()
            self.next_button.config(state=tk.DISABLED)
            self.prev_button.config(state=tk.DISABLED)
            self.save_state()
        else:
            # Assume all files are processed if no more files are left to process
            self.on_exit()

    def update_filename(self):
        filename = os.path.basename(self.file_list[self.current_file_index])
        self.filename_entry.delete(0, tk.END)
        self.filename_entry.insert(0, filename)
        title = f"Audio Categorization Tool - File {self.current_file_index + 1} of {len(self.file_list)}"
        title += f" (subject name: {self.folder_name})"
        self.master.title(title)
        self.selection_made = False

    def reset_selection(self):
        self.category_var.set("None")
        for cb in self.check_buttons.values():
            cb.deselect()

    def save_response(self):
        # Save the current response to the dataframe
        coder = self.coder_name_entry.get()
        coding_result = self.category_var.get().split()[0]
        coding_result = coding_result.strip('() 😢😱😫😮🚫🤔')  # Cleaning the coding result to save only the number
        def convert_string_to_number(text):
            # Define a dictionary mapping specific strings to numbers
            mapping = {
                "Cry": 1,
                "Scream": 2,
                "Whine/Fuss": 3,
                "Yelling": 4,
                "None": 5,
                "Not": 6

            }
            # Return the corresponding number if the text matches, otherwise return None
            return mapping.get(text, None)  # Returns None if the text is not found
        coding_result = convert_string_to_number(coding_result)

        # Correcting how data is saved to ensure all fields are correctly updated or maintained
        self.df.loc[self.current_file_index, 'coder'] = coder
        self.df.loc[self.current_file_index, 'coding_result'] = coding_result

        # Ensuring folder name and file index are maintained
        self.df.loc[self.current_file_index, 'folder_name'] = self.folder_name
        self.df.loc[self.current_file_index, 'file_idx'] = self.current_file_index

        # Save the dataframe to pickle every time a change is made
        self.df.to_pickle(self.dataframe_path)

    def load_responses(self):
        # Load responses if they exist, and update the UI accordingly
        for idx, row in self.df.iterrows():
            if pd.notna(row['coding_result']):
                category = f"{row['coding_result']} "
                for key, cb in self.check_buttons.items():
                    if category in key:
                        cb.select()
                        break
                self.category_var.set(category)


    # def get_state_filename(self):
    #     # Extract the last directory name from the file directory path
    #     folder_name = os.path.basename(self.file_directory)
    #     state_filename = f"state-{folder_name}.txt"
    #     return state_filename
    def save_state(self):
        state_filename = self.state_file_path
        with open(state_filename, 'w') as f:
            # Check if all files have been coded
            completed = 'done' if not self.df['coding_result'].isnull().any() else 'incomplete'
            f.write(f"{self.current_file_index}\n{completed}\n")

    def save_coder_name(self):
        coder_name = self.coder_name_entry.get()
        with open('bookmark/codername.txt', 'w') as f:
            f.write(coder_name)

    def load_coder_name(self):
        if os.path.exists('bookmark/codername.txt'):
            with open('bookmark/codername.txt', 'r') as f:
                coder_name = f.readline().strip()
                self.coder_name_entry.delete(0, tk.END)
                self.coder_name_entry.insert(0, coder_name)

    def load_state(self):
        state_filename = self.state_file_path
        if os.path.exists(state_filename):
            with open(state_filename, 'r') as f:
                lines = f.readlines()
                if lines:
                    self.current_file_index = int(lines[0].strip())
                    self.coding_complete = True if lines[1].strip() == 'done' else False
                    self.update_filename()

    def show_completion_message(self):
        # Display a completion message at the end of the coding for the current subject
        msgbox.showinfo("Completion Message",
                        f"Coding is done on subject name {self.folder_name}. Click OK to finish the program.")

    def on_exit(self):
        # Ensure all responses are saved before checking if the work is complete
        self.save_response()  # Save the current progress
        self.save_state()  # Update the saved state

        # Check if coding is actually complete
        if not self.df['coding_result'].isnull().any():
            self.show_completion_message()

        # Stop any audio that is currently playing
        self.stop_audio()

        # Save the DataFrame to CSV and clean up
        self.df.to_csv(self.results_path, index=False)
        self.master.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioPlayerGUI(root)
    root.mainloop()
