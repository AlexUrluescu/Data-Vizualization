
set -e

cd "$(dirname "$0")"

echo "Starting Flask Server with uv..."

uv run app.py