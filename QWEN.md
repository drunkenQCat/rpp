# RPP Project Context

## Project Overview

RPP is a Python library designed to parse and emit REAPER RPP (REAPER Project) files. REAPER is a digital audio workstation (DAW) that uses the RPP format to store project information. This library provides functionality to read, manipulate, and write RPP files programmatically.

The project uses PLY (Python Lex-Yacc) as a parser framework to handle the RPP format, which appears to be a hierarchical text format with tags and attributes similar to XML but with a custom syntax.

### Key Features
- Parse RPP files into Python objects
- Generate RPP files from Python objects
- Provides an Element interface similar to xml.etree.ElementTree.Element
- Supports querying operations with findall, find, and iterfind methods
- Handles complex RPP structures with nested elements and various data types

### Architecture
The project consists of several core modules:
- `rpp.py`: Main entry point with load/dump functions
- `element.py`: Defines the Element class that represents RPP elements using dataclasses
- `encoder.py`: Serializer that converts Element trees back to RPP format
- `tokenizer.py`: Tokenizer that handles lexical analysis of RPP content using lark

## Building and Running

### Dependencies
- `lark`: For parsing RPP content using a lexer and parser
- `dataclasses`: Standard library module for defining classes with less boilerplate (Python 3.7+)

### Setup
```bash
# Install dependencies
pip install attrs ply

# Or install the package in development mode
pip install -e .
```

### Testing
The project uses pytest for testing:

```bash
# Run tests with pytest
pytest

# Or use tox to run tests across multiple Python versions
tox
```

### Linting
The project includes flake8 linting:

```bash
# Run flake8 linting
tox -e flake8
```

## Development Conventions

### Code Style
- Follows Python PEP 8 style guidelines
- Uses dataclasses for class definitions
- Includes comprehensive docstrings and type hints where appropriate

### Testing Practices
- Comprehensive unit tests covering parsing and serialization
- Parametrized tests for different file formats
- Round-trip conversion tests to ensure data integrity
- Edge case testing for special characters and formatting

### File Format Support
The RPP format supports:
- Hierarchical elements with `<TAG ... >` syntax
- Nested elements
- Various data types (strings, numbers, binary data)
- Special handling for quoted strings with different quote marks
- Multi-line content with pipe (`|`) prefixes

## Key Data Structures

### Element Class
The core `Element` class mimics the interface of `xml.etree.ElementTree.Element` and provides:
- `tag`: The element tag name
- `attrib`: A tuple of attributes
- `children`: A list of child elements
- Methods for finding and manipulating child elements

### Example Usage
```python
import rpp

# Load an RPP file
with open('project.rpp', 'r') as f:
    project = rpp.load(f)

# Or parse from string
project = rpp.loads(rpp_string)

# Manipulate the project structure
for element in project.findall('.//TRACK'):
    # Modify track properties
    pass

# Save back to RPP format
with open('modified_project.rpp', 'w') as f:
    rpp.dump(project, f)
```

## Project Structure
```
rpp/
├── __init__.py          # Package exports
├── rpp.py              # Main API functions (load, dump, loads, dumps)
├── element.py          # Element class definition using dataclasses
├── encoder.py          # Serialization logic
└── tokenizer.py        # Lexical analysis and parsing using lark
tests/
├── test_rpp.py         # Core functionality tests
├── test_element.py     # Element class tests
└── data/               # Test data files
```

## Version Information
- Current version: 0.5
- Python compatibility: >= 3.7
- Status: Beta (4 - Beta)

## Qwen Added Memories
- 在当前项目中使用 uv 作为包管理器：运行 Python 命令时使用 'uv run'，安装依赖时使用 'uv add'
