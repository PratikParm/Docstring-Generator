# Docstring-Generator

A tool to automatically generate Google-style docstrings for Python functions and classes using a local LLM.

## Features

- Analyzes Python code to find all functions and classes.
- Uses an LLM to generate high-quality docstrings.
- Inserts generated docstrings into the correct places in the code.
- Outputs annotated code to a specified directory, preserving the original structure.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/Docstring-generator.git
cd Docstring-generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
## Usage

1. Prepare your source code
Place your Python codebase in a directory, e.g., my_project/.

2. Run the docstring generator
```python
python scripts/generate_docstrings.py --source_dir my_project --output_dir annotated_project
```

* --source_dir: Path to your source code directory.
* --output_dir: Path where annotated files will be saved.

