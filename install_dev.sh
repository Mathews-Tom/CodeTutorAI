#!/bin/bash

# Install the package in development mode
pip install -e .

# Create symbolic links for the node modules
mkdir -p src/enlightenai/nodes
for file in nodes/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "__init__.py" ]; then
            ln -sf "../../../$file" "src/enlightenai/nodes/$filename"
        fi
    fi
done

# Create symbolic links for the utility modules
mkdir -p src/enlightenai/utils
for file in utils/*.py; do
    if [ -f "$file" ]; then
        filename=$(basename "$file")
        if [ "$filename" != "__init__.py" ]; then
            ln -sf "../../../$file" "src/enlightenai/utils/$filename"
        fi
    fi
done

echo "Development installation complete!"
