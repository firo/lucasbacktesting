# Use the latest Debian as the base image
FROM debian:latest

# Set environment variables to prevent interactive prompts during installation
ENV DEBIAN_FRONTEND=noninteractive

# Update the package list and install necessary packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    git \
    libfreetype6-dev \
    libpng-dev \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Clone the GitHub repository
RUN git clone https://github.com/firo/lucasbacktesting.git .

# Install Python dependencies individually
RUN pip3 install --no-cache-dir \
    backtrader \
    yfinance \
    streamlit \
    pandas \
    matplotlib

# Expose the Streamlit port
EXPOSE 8502

# Command to run the Streamlit app
CMD ["streamlit", "run", "firo_ui.py", "--server.port=8502"]
