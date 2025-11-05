#!/bin/bash
# Create tree-sitter directory
mkdir -p ~/.tree-sitter

# Clone language repositories
cd ~/.tree-sitter

# Common languages
for lang in python javascript typescript go java ruby rust cpp; do
    if [ ! -d "tree-sitter-$lang" ]; then
        git clone "https://github.com/tree-sitter/tree-sitter-$lang"
    fi
done