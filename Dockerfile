# Use the official Python image from the Docker Hub
FROM python:3.12.7-slim

# Set the working directory in the container
WORKDIR /app

# Copy the contents of the flask directory into the container
COPY flask/ .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

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

# Remove Windows line endings
RUN sed -i -e 's/\r$//' start.sh

# Ensure start.sh is executable
RUN chmod +x start.sh

# Add HEALTHCHECK
HEALTHCHECK --interval=15s --timeout=10s --start-period=30s --retries=3 CMD curl -f http://localhost:5000/health | grep -q "Healthy" || bash -c 'kill -s 15 -1 && (sleep 10; kill -s 9 -1)'

# Run start.sh
CMD ["./start.sh"]
