import numpy as np
import pandas as pd
import subprocess
import sys
import os

# Generate data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Define the filename dynamically, you can change this to any name
filename = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tests", 'data_sine_wave.csv')

# Save data to the CSV file with the dynamic filename
data = pd.DataFrame({'x': x, 'y': y})
data.to_csv(filename, index=False)

dir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "tests", "create_plot.r")

# Check the path to the R script
print(f"R script path: {dir}")

# Now call the external R script and pass the filename to it as a command-line argument
try:
    subprocess.run(['Rscript', dir], check=True)  # check=True ensures the error is raised if Rscript fails
except FileNotFoundError as e:
    print(f"Error: {e}")
except subprocess.CalledProcessError as e:
    print(f"Error: {e}")