# Get the filename from the command-line argument
args <- commandArgs(trailingOnly = TRUE)
filename <- args[1]

# Check if the filename is provided
if (is.null(filename)) {
  stop("No filename provided!")
}

# Load the data from the specified CSV file
data <- read.csv(filename)

# Create the plot
plot(data$x, data$y, type='l', col='blue', lwd=2, main='Sine Wave', xlab='X', ylab='Y')

# Optionally, save the plot to a file, e.g., 'plot.png'
# dev.copy(png, "plot.png")
# dev.off()
