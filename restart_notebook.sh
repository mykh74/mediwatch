#!/bin/bash

# Restart Notebook Helper Script for MediWatch
# This script helps clear notebook outputs before rerunning

echo "=================================================="
echo "MediWatch - Notebook Restart Helper"
echo "=================================================="
echo ""

# Navigate to project root
cd /Users/michaelkuzmyn/projects/ik/MediWatch

# Activate virtual environment
echo "✓ Activating virtual environment..."
source .venv/bin/activate

echo "✓ Virtual environment activated"
echo ""
echo "The notebook has been fixed. Old execution errors are cached."
echo ""
echo "To run the notebook without errors, follow these steps:"
echo ""
echo "1. In VS Code:"
echo "   - Press Cmd+Shift+P"
echo "   - Type: 'Notebook: Restart Kernel'"
echo "   - Then: 'Notebook: Clear All Outputs'"
echo "   - Finally: 'Run All Cells'"
echo ""
echo "OR"
echo ""
echo "2. Open in Jupyter:"
echo "   jupyter notebook notebooks/02_model_training.ipynb"
echo "   Then click: Kernel → Restart & Clear Output → Run All"
echo ""
echo "=================================================="
