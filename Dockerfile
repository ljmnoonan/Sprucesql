# Use an official Python runtime as a parent image that is ARM64 compatible
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for the MS ODBC Driver
# The 'accept-eula' is crucial for non-interactive installation
RUN apt-get update && apt-get install -y curl gnupg lsb-release

# Add Microsoft's official repository for Ubuntu
# Download the Microsoft GPG key and store it in the keyrings directory
RUN curl -sSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > /usr/share/keyrings/microsoft-prod.gpg

# Create the repository source list file for Debian 12 (Bookworm)
RUN echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql-release.list

# Update package lists and install the driver
RUN apt-get update
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql18

# Copy the file that lists the Python dependencies
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY app.py .

# Expose the port the app runs on
EXPOSE 5000

# Define the command to run the application
CMD ["flask", "run"]
