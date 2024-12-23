# Use the latest Debian as the base image
FROM debian:latest

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Clone the GitHub repository
RUN git clone https://github.com/firo/lucasbacktesting.git .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the Streamlit port
EXPOSE 8502

# Command to run the Streamlit app
CMD ["streamlit", "run", "firo_ui.py", "--server.port=8502"]
