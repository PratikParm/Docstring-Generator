class Reader:
    def __init__(self):
        pass

    def analyze_component(self, component):
        dependency_ids = [dep.component_id
                          for dep 
                          in component.dependencies]
        
        external_refs = []
        usage_refs = component.type == 'class'

        context_request = {
            'component_id': component.component_id,
            'dependencies': dependency_ids,
            'external_refs': external_refs,
            'usage_refs': usage_refs,
        }

        return context_request