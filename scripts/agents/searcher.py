import os
import re

class Searcher:
    def __init__(self, source_dir):
        self.source_dir = source_dir
    
    def load_component_code(self, component_id):
        file_path, component_name = component_id.split(':', 1)
        full_path = os.path.join(self.source_dir, file_path)

        if not os.path.isfile(full_path):
            return None

        with open(full_path, 'r', encoding='utf-8') as file:
            code = file.read()
        
        return code
    
    def search(self, context_request):
        main_code = self.load_component_code(context_request['component_id'])

        dependency_sources = {}

        for dep_id in context_request.get('dependencies', []):
            dep_code = self.load_component_code(dep_id)
            if dep_code:
                dependency_sources[dep_id] = dep_code

        external_refs = context_request.get('external_refs', [])
        usage_refs = []
        if context_request.get('usage_refs', False):
            usage_refs = self.find_usage_references(context_request['component_id'])

        return {
            'component_id': context_request['component_id'],
            'source_code': main_code,
            'dependency_sources': dependency_sources,
            'external_refs': external_refs,
            'usage_refs': usage_refs
        }
    
    def find_usage_references(self, component_id):
        filepath, component_name = component_id.split(':', 1)
        pattern = re.compile(rf'\b{re.escape(component_name)}\b')
        usage_refs = []

        for root, _, files in os.walk(self.source_dir):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    for lineno, line in enumerate(lines, start=1):
                        if pattern.search(line):
                            usage_refs.append({
                                'file': full_path,
                                'line': lineno,
                                'code': line.strip()
                            })
        return usage_refs