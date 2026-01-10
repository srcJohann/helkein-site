#!/bin/bash

# Define variables
REMOTE_USER="root"
REMOTE_HOST="69.6.243.123"
REMOTE_DIR="/root/helkein-site"
SSH_PORT="22022"
SSH_PASS="~aR3PT_>-Jik"
# Combine options: Port and Algorithms
SSH_OPTS="-p $SSH_PORT -o HostKeyAlgorithms=+ssh-rsa -o PubkeyAcceptedAlgorithms=+ssh-rsa"

echo "-------------------------------------------------------"
echo "Deploying to $REMOTE_USER@$REMOTE_HOST on port $SSH_PORT"
echo "Password: $SSH_PASS"
echo "(Copy the password above if prompted)"
echo "-------------------------------------------------------"

# Create the remote directory if it doesn't exist
# We use the specific SSH options (port and algorithms)
ssh $SSH_OPTS $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_DIR"

# Rsync command
# Included -e "ssh $SSH_OPTS" to pass the port and algorithms to the underlying ssh connection used by rsync
rsync -avz --progress --exclude-from='.gitignore' --exclude='.git' -e "ssh $SSH_OPTS" . "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR"

echo "Deploy finished."
