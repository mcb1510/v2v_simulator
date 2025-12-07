# V2VSimulator

Group:

- Brodie Abrew
- Phuc Le
- Miguel Carrasco Belmar
- Ricardo Rodriguez
- Alex Curtis
- Tasvi Adappa

## Project Description

This is a Python simulation of a vehicle-to-vehicle network. It displays a tabular view of simulated vehicles alongside a basic message
log of both basic safety messages (BSMs) and collision warning messages (CWMs).
A live statistics view is also presented with the following information:

- Current simulation time
- Number of vehicles present
- Number of BSMs and CWMs sent
- Number of prevented collisions
- The current time ratio e.g. 1x for normal time speed; 2x for double time speed

## Development Setup

Here are the steps to set up the development environment for the V2VSimulator project. You should only need to do this
once. _You may need to rerun step #4 if new dependencies are added to `requirements.txt`._

### 1. Ensure you have Python 3.12+ installed.

- Minimum required version is 3.10 per minimum dependencies, but 3.12+ is recommended.
- It is recommended to use a python version manager such as `pyenv` or `asdf` to manage multiple python versions on your machine.
- Switch to the desired python version using your version manager, before proceeding to the next steps.

### 2. Create a virtual Python environment using the following command:

- Run `python --version` to confirm you are using the desired python version before running the following command.
- Whichever version is returned by the above command will be the version used in the virtual environment.

```
python -m venv .venv
```

This creates a `.venv/` directory and a virtual environment within it. Do NOT commit this directory to version control.

### 3. Activate the virtual Python environment as described in step 1 of [usage](#usage).

### 4. Install required dependencies:

```
pip install -r requirements.txt
```

## Usage

### 1. Activate the Python virtual environment:

Linux/Mac:

```
source .venv/bin/activate # bash/zsh shell
```

Windows:

```
.venv\Scripts\activate.bat # Command prompt
.venv\Scripts\activate.ps1 # PowerShell
```

2. Run the `basic_simulator` using the following command:

```
python ./basic_simulator/simulator.py
```

### Using the V2V Simulator CLI

The project includes a command-line interface for running V2V network simulations with live statistics and visualization.

**Basic Usage:**

```bash
python v2v-simulator.py
```

This runs a 30-second simulation with 10 vehicles and displays live updates in your terminal.

**Common Options:**

```bash
# Run for 60 seconds with 20 vehicles
python v2v-simulator.py -d 60 -v 20

# Save statistics to a JSON file
python v2v-simulator.py --output results.json

# Custom configuration
python v2v-simulator.py --duration 45 --vehicles 15 --max-messages 50
```

**Available Options:**

- `-d, --duration` - Simulation duration in seconds (default: 30)
- `-v, --vehicles` - Number of vehicles to spawn (1-100, default: 10)
- `--output` - Save final statistics to a JSON file
- `--max-messages` - Maximum messages to display in log (default: 25)
- `--help` - Show all available options

**What You'll See:**

The CLI displays:

- **Vehicle States** - Real-time position, velocity, and acceleration for each vehicle
- **Live Statistics** - BSM/CWM message counts, collisions prevented, simulation speed
- **Message Log** - Recent BSM (Basic Safety Messages) and CWM (Collision Warning Messages)
- **Configuration** - Current simulation parameters

Press `Ctrl+C` to stop the simulation early.
