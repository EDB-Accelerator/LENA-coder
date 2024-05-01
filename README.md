![Screenshot](https://github.com/EDB-Accelerator/LENA-coder/blob/main/screenshot.png?raw=true)

# Audio Categorization Tool

This tool is designed to help categorize audio files into different categories such as Cry, Scream, Whine/Fuss, Yelling, None, or Not Sure. It provides a graphical user interface (GUI) for users to listen to audio files and select the appropriate category for each file.

## Installation

### Python Environment Setup

1. Clone the repository to your local machine:
```bash
git clone git@github.com:EDB-Accelerator/LENA-coder.git
```
Alternately, download the repository as a ZIP file by clicking [here](https://github.com/leekh3/LENA-coder/archive/refs/heads/main.zip).

2. Navigate to the extracted directory using a terminal or command prompt.

3. Create and activate a Python 3.8 Anaconda environment using the provided `py38.yml` file:
```bash
conda env create -f py38.yml
conda activate py38
```

### Additional Setup for macOS Users

If you're using macOS, you need to install `portaudio` using Homebrew. If you haven't installed Homebrew yet, you can do so by following the instructions [here](https://brew.sh). Once Homebrew is installed, run the following command on your Terminal:
```bash
brew install portaudio
```

## Usage

1. Run the Python script `audio_categorization_tool.py`.
2. The GUI will prompt you to select the folder containing the audio files you want to categorize.
3. Once the folder is selected, the tool will display the first audio file in the folder.
4. Listen to the audio file and select the appropriate category using the provided options.
5. Use the "Next" button to move to the next audio file and repeat the process until all files are categorized.
6. If you need to skip to a specific file, you can use the "Skip to" button and enter the file number index.
7. The tool will save your categorization responses automatically as you progress.
8. Once all files are categorized, the tool will display a completion message. You can find the coding results in the results folder.
9. You can delete the state file for each subject from the bookmark folder if you want to start categorizing from the beginning.

## Dependencies

- Python 3.8
- Pygame
- Glob
- Pydub
- Pyaudio
- Matplotlib
- Numpy
- Pandas
- Tkinter

## Authors
- Kyunghun Lee (National Institutes of Health)
- Lauren Henry (National Institutes of Health)
- Ellie Hansen (National Institutes of Health)

Advised by Melissa Brotman (National Institutes of Health)


## License
This tool was originally developed for the LENA project by the Neuroscience and Novel Therapeutics Unit (NNT) at the National Institutes of Health; however, it is open for use by anyone. This project is licensed under the MIT License. For more information, see the [LICENSE](https://www.mit.edu/~amini/LICENSE.md)  for details.
