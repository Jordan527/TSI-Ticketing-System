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

# Set the authtoken for ngrok
RUN ngrok config add-authtoken 2cJ8E4Ue6Yyt08bNLtnhe9re05A_6Cccz8gQ7gzgrpv9SAu5E

# Wait for Flask to be running before executing the curl command
CMD ["sh", "-c", "ngrok http --domain=arguably-chief-colt.ngrok-free.app 5000 & flask --debug run --host=0.0.0.0 --port=5000 & while ! curl -s http://localhost:5000/health > /dev/null; do sleep 1; done; curl -X POST http://localhost:5000/initialise || true; wait"]