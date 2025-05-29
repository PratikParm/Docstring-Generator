import os
import ast
from collections import defaultdict, deque

class CodeComponent:
    def __init__(self, name, component_type, filepath, node):
        self.name = name
        self.component_id = f"{filepath}:{name}:{component_type}"
        self.type = component_type
        self.filepath = filepath
        self.node = node
        self.dependencies = set()

    def __hash__(self):
        # For set and dict keys, consider name + filepath + type to distinguish
        return hash((self.name, self.filepath, self.type))

    def __eq__(self, other):
        return (self.name, self.filepath, self.type) == (other.name, other.filepath, other.type)

    def __repr__(self):
        return f"{self.type}: {self.name} ({self.filepath})"


from collections import defaultdict, deque

class DependencyGraph:
    def __init__(self):
        self.nodes = {}  # key = (filepath, name), value = CodeComponent
        self.edges = defaultdict(set)  # adjacency list

    def add_node(self, component):
        key = (component.filepath, component.name)
        self.nodes[key] = component

    def add_edge(self, from_component, to_component):
        from_key = (from_component.filepath, from_component.name)
        to_key = (to_component.filepath, to_component.name)
        self.edges[from_key].add(to_key)

    def tarjan_scc(self):
        """Find strongly connected components using Tarjan's algorithm."""
        index = 0
        stack = []
        on_stack = set()
        indices = {}
        lowlink = {}
        sccs = []

        def strongconnect(node):
            nonlocal index
            indices[node] = index
            lowlink[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)

            for neighbor in self.edges.get(node, []):
                if neighbor not in indices:
                    strongconnect(neighbor)
                    lowlink[node] = min(lowlink[node], lowlink[neighbor])
                elif neighbor in on_stack:
                    lowlink[node] = min(lowlink[node], indices[neighbor])

            # If node is root of SCC
            if lowlink[node] == indices[node]:
                scc = []
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.append(w)
                    if w == node:
                        break
                sccs.append(scc)

        for node in self.nodes:
            if node not in indices:
                strongconnect(node)

        return sccs

    def build_condensed_graph(self, sccs):
        """
        Build a new graph where each SCC is a single node.
        Returns:
          - condensed_nodes: list of SCCs (each SCC is a list of node keys)
          - condensed_edges: adjacency dict mapping SCC index to set of SCC indices
        """
        # Map node to SCC index
        node_to_scc = {}
        for i, scc in enumerate(sccs):
            for node in scc:
                node_to_scc[node] = i

        condensed_edges = defaultdict(set)
        for from_node, to_nodes in self.edges.items():
            from_scc = node_to_scc[from_node]
            for to_node in to_nodes:
                to_scc = node_to_scc[to_node]
                if from_scc != to_scc:
                    condensed_edges[from_scc].add(to_scc)

        return sccs, condensed_edges

    def topological_sort_condensed(self, condensed_edges, num_nodes):
        """Topologically sort the condensed DAG."""
        in_degree = [0] * num_nodes
        for from_node, neighbors in condensed_edges.items():
            for neighbor in neighbors:
                in_degree[neighbor] += 1

        queue = deque([i for i, deg in enumerate(in_degree) if deg == 0])
        sorted_scc_indices = []

        while queue:
            current = queue.popleft()
            sorted_scc_indices.append(current)
            for neighbor in condensed_edges.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_scc_indices) != num_nodes:
            raise ValueError("Cycle detected in condensed graph - this should not happen")

        return sorted_scc_indices

    def topological_sort(self):
        """
        Returns a list of CodeComponent lists, where each list is an SCC group of components.
        Single-node SCCs have one component.
        """
        sccs = self.tarjan_scc()
        condensed_nodes, condensed_edges = self.build_condensed_graph(sccs)
        sorted_scc_indices = self.topological_sort_condensed(condensed_edges, len(condensed_nodes))

        # Map SCC index to list of components
        scc_components = []
        for scc in condensed_nodes:
            comp_list = [self.nodes[node_key] for node_key in scc]
            scc_components.append(comp_list)

        # Return components in topological order of SCC groups
        sorted_components = []
        for idx in sorted_scc_indices:
            sorted_components.append(scc_components[idx])

        return sorted_components


def parse_code(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        source = file.read()
    tree = ast.parse(source)
    components = []

    class DependencyVisitor(ast.NodeVisitor):
        def __init__(self):
            self.current_component = None
        
        def visit_FunctionDef(self, node):
            component = CodeComponent(node.name, 'function', filepath, node)
            self.current_component = component
            self.generic_visit(node)
            components.append(component)
            self.current_component = None

        def visit_AsyncFunctionDef(self, node):
            component = CodeComponent(node.name, 'async_function', filepath, node)
            self.current_component = component
            self.generic_visit(node)
            components.append(component)
            self.current_component = None
        
        def visit_ClassDef(self, node):
            component = CodeComponent(node.name, 'class', filepath, node)
            self.current_component = component
            self.generic_visit(node)
            components.append(component)
            self.current_component = None

        def visit_Call(self, node):
            # Handle function or method calls inside components
            if self.current_component:
                # Function calls like foo()
                if isinstance(node.func, ast.Name):
                    callee_name = node.func.id
                    callee_comp = CodeComponent(callee_name, 'function', None, node)
                    self.current_component.dependencies.add(callee_comp)
                # Method calls like obj.method()
                elif isinstance(node.func, ast.Attribute):
                    callee_name = node.func.attr
                    callee_comp = CodeComponent(callee_name, 'method', None, node)
                    self.current_component.dependencies.add(callee_comp)
            self.generic_visit(node)

    visitor = DependencyVisitor()
    visitor.visit(tree)
    return components


def build_dependency_graph(source_dir):
    graph = DependencyGraph()
    all_components = []

    for root, _, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                components = parse_code(filepath)
                for comp in components:
                    graph.add_node(comp)
                all_components.extend(components)

    # Build edges by matching dependencies by name and type ignoring filepath for dependency (which may be None)
    for component in all_components:
        for dep in list(component.dependencies):
            matches = [node for node in graph.nodes.values() if node.name == dep.name and node.type == dep.type]
            for matched_comp in matches:
                graph.add_edge(component, matched_comp)

    return graph


def get_source_segment(filepath, node):
    """Extract source code segment of node using lineno and end_lineno."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    start = node.lineno - 1
    end = getattr(node, "end_lineno", node.lineno)
    return "".join(lines[start:end])


def build_component_dicts(sorted_components):
    comp_id_map = {}
    for comp in sorted_components:
        comp_id = f"{comp.filepath}::{comp.name}::{comp.type}"
        comp_id_map[(comp.filepath, comp.name, comp.type)] = comp_id
    
    components_list = []
    for comp in sorted_components:
        comp_id = comp_id_map[(comp.filepath, comp.name, comp.type)]
        source_code = get_source_segment(comp.filepath, comp.node)

        dep_ids = []
        for dep in comp.dependencies:
            resolved = None
            for key, cid in comp_id_map.items():
                if key[1] == dep.name and key[2] == dep.type:
                    resolved = cid
                    break
            if resolved:
                dep_ids.append(resolved)

        components_list.append({
            "component_id": comp_id,
            "source_code": source_code,
            "dependencies": dep_ids,
            "type": comp.type,
            "name": comp.name,
            "filepath": comp.filepath,
        })

    return components_list


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Navigator: build dependency graph and sort components")
    parser.add_argument("--source_dir", type=str, required=True, help="Root source directory to scan")
    args = parser.parse_args()

    graph = build_dependency_graph(args.source_dir)
    sorted_components = graph.topological_sort()

    print("Topologically sorted components:")
    for comp in sorted_components:
        print(comp)
