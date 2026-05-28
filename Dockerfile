# Use a slim Python image for a smaller, faster container
FROM python:3.10-slim

# Copy the uv binary directly from Astral's official Docker image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Create a user to avoid running as root (Hugging Face requirement)
RUN useradd -m -u 1000 user
USER user

# Set environment variables
# UV_COMPILE_BYTECODE speeds up app startup
# UV_LINK_MODE prevents caching errors inside Docker
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Set the initial working directory
WORKDIR $HOME/app

# Copy all your project files into the container
COPY --chown=user . $HOME/app

# Change into your backend folder where pyproject.toml and uv.lock live
WORKDIR $HOME/app/backend

# Sync dependencies using uv (this uses your uv.lock file)
# --frozen ensures it doesn't try to update your lockfile
# --no-dev skips installing testing/development libraries
RUN uv sync --frozen --no-dev

# Expose the Hugging Face port
EXPOSE 7860

# Command to run your app using uv's virtual environment
CMD ["uv", "run", "python", "app.py"]