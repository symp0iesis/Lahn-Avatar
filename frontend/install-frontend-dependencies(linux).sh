# Update package list
sudo apt update

# Install curl if not already installed
sudo apt install curl -y

# Install Node.js (LTS version) using NodeSource
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs

# Verify installations
node -v
npm -v
