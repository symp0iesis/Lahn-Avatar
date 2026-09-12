#!/bin/bash
set -e
cd /root/AvatarGarden/backend
export PATH="/root/AvatarGarden/env/bin:$PATH"
export VIRTUAL_ENV="/root/AvatarGarden/env"
# Disable all progress bars and interactive prompts
export TRANSFORMERS_VERBOSITY=error
export HF_HUB_DISABLE_PROGRESS_BARS=1
export HF_HUB_DISABLE_EXPERIMENTAL_WARNING=1
export TQDM_DISABLE=1
# Ensure stdout/stderr are unbuffered
exec /root/AvatarGarden/env/bin/python -u server.py

