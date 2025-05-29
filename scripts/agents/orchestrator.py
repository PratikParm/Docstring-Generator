import os
from .reader import Reader
from .searcher import Searcher
from .writer import Writer
from .verifier import Verifier
from collections import defaultdict


class Orchestrator:
    def __init__(self, graph, source_dir, output_dir, llm_client=None):
        self.graph = graph
        self.source_dir = source_dir
        self.output_dir = output_dir
        self.reader = Reader()
        self.searcher = Searcher(source_dir)
        self.writer = Writer(source_dir, output_dir, llm_client)
        self.verifier = Verifier()

        os.makedirs(self.output_dir, exist_ok=True)

    def run(self):
        sorted_scc_groups = self.graph.topological_sort()
        # Flatten all components and group by file
        file_to_components = defaultdict(list)
        for group in sorted_scc_groups:
            for component in group:
                file_to_components[component.filepath].append(component)
        for filepath, components in file_to_components.items():
            print(f"Processing file: {filepath} with {len(components)} components")
            self.process_file(filepath, components)

    def process_file(self, filepath, components):
        # For each component, build context and generate docstring
        components_contexts = []
        for component in components:
            context = self.reader.analyze_component(component)

            searched_context = self.searcher.search(context)

            dependency_sources = searched_context.get('dependency_sources', {})
            usage_refs = searched_context.get('usage_refs', [])
            external_refs = searched_context.get('external_refs', [])
            context.update({
                'dependency_sources': dependency_sources,
                'external_refs': external_refs,
                'usage_refs': usage_refs
            })
            context['name'] = component.name
            context['type'] = component.type
            context['component_id'] = f"{component.filepath}:{component.name}"
            docstring = self.writer.generate_docstring(context)
            context['docstring'] = docstring

            verification_report = self.verifier.verify_docstring(context)
            print(f"Verification report for {component.component_id}: {verification_report}")
            components_contexts.append(context)
        # Save the annotated file with all docstrings inserted
        self.writer.write_docstrings_for_file(filepath, components_contexts)