# Use the official Python image from the Docker Hub
FROM python:3.12.7

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Install curl
RUN apt-get update && apt-get install -y curl

# Install tar
RUN apt-get update && apt-get install -y tar

# Install ngrok
RUN curl https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o ngrok-stable-linux-amd64.tgz
RUN tar -xvf ngrok-stable-linux-amd64.tgz
RUN mv ngrok /usr/local/bin

# Ensure start.sh is executable
RUN chmod +x start.sh

# Run start.sh
CMD ["./start.sh"]