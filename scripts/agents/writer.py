import os
import re

class Writer:
    def __init__(self, source_dir, output_dir, llm_client=None):
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.llm_client = llm_client

    def generate_docstring(self, context):
        source_code = context.get('source_code', '')
        dependencies = context.get('dependency_sources', {})
        external_refs = context.get('external_refs', [])
        usage_refs = context.get('usage_refs', [])

        prompt = (
            "Generate a Python docstring for the following code. "
            "The docstring should summarize the component in one line, list input parameters with types and descriptions, and describe the return value. "
            "Use Google-style docstrings.\n\n"
            "Code:\n"
            "def add_numbers(a: float, b: float) -> float:\n"
            "    return a + b\n"
            "Docstring:\n"
            '"""\n'
            "Add two numbers and return the result.\n\n"
            "Args:\n"
            "    a (float): The first number.\n"
            "    b (float): The second number.\n\n"
            "Returns:\n"
            "    float: The sum of the two input numbers.\n"
            '"""\n\n'
            "Code:\n"
            "class Person:\n"
            "    def __init__(self, name: str, age: int):\n"
            "        self.name = name\n"
            "        self.age = age\n\n"
            "    def greet(self) -> str:\n"
            "        return f'Hello, my name is ' _ self.name\n"
            "Docstring:\n"
            '"""\n'
            "Represents a person with a name and age.\n\n"
            "Attributes:\n"
            "    name (str): The name of the person.\n"
            "    age (int): The age of the person.\n\n"
            "Methods:\n"
            "    greet(): Returns a greeting string.\n"
            '"""\n\n'
            "Source Code:\n{source_code}\n\n"
            "Dependencies:\n{dependencies}\n\n"
            "External references:\n{external_refs}\n\n"
            "Usage references:\n{usage_refs}\n"
            "Docstring:"
        ).format(
            source_code=source_code,
            dependencies=dependencies,
            external_refs=external_refs,
            usage_refs=usage_refs
        )

        if self.llm_client:
            docstring = self.llm_client.generate_docstring(prompt)
        else:
            docstring = "Placeholder docstring: describe the function or class"
        return docstring

    def insert_docstrings_bulk(self, original_code, components):
        """
        Insert docstrings for all components (functions/classes) in the file.
        components: list of dicts with 'name', 'type', and 'docstring'.
        """
        lines = original_code.split('\n')
        insertions = []
        for comp in components:
            # Use a robust regex pattern with f-string and raw string
            pattern = re.compile(rf"^(\s*)(def|class)\s+{re.escape(comp['name'])}\b.*:")
            found = False
            for i, line in enumerate(lines):
                match = pattern.match(line)
                if match:
                    found = True
                    # Check if next non-empty, non-comment line is a docstring
                    j = i + 1
                    while j < len(lines) and (lines[j].strip() == '' or lines[j].strip().startswith('#')):
                        j += 1
                    if j < len(lines) and (lines[j].strip().startswith('"""') or lines[j].strip().startswith("'''")):
                        # Existing docstring found, skip
                        break
                    indent = match.group(1) + ' ' * 4
                    docstring_lines = [f'{indent}"""', f'{indent}{comp["docstring"]}', f'{indent}"""']
                    insertions.append((i + 1, docstring_lines))
                    break
            if not found:
                print(f"[DEBUG] No match found for component: {comp['name']}")
        # Insert docstrings from bottom to top to avoid messing up indices
        for idx, docstring_lines in sorted(insertions, reverse=True):
            lines[idx:idx] = docstring_lines
        return '\n'.join(lines)

    def write_docstrings_for_file(self, filepath, components_contexts):
        """
        For a given file, insert docstrings for all components (using pre-generated docstrings), and write the updated code to output_dir.
        components_contexts: list of context dicts for each component in the file.
        """
        # Always use the full path to the source file
        full_path = filepath
        with open(full_path, 'r', encoding='utf-8') as file:
            original_code = file.read()
        # Use pre-generated docstrings for all components
        components = []
        for context in components_contexts:
            docstring = context.get('docstring')
            if not docstring:
                docstring = self.generate_docstring(context)
            components.append({'name': context['name'], 'type': context['type'], 'docstring': docstring})
        updated_code = self.insert_docstrings_bulk(original_code, components)
        output_path = os.path.join(self.output_dir, filepath)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(updated_code)
        print(f"Wrote docstrings for {filepath} to {output_path}")