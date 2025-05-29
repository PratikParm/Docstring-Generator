class Verifier:
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def verify_docstring(self, context):
        component_id = context['component_id']
        docstring = context.get('docstring', '')
        source_code = context.get('source_code', '')
        dependencies = context.get('dependency_sources', {})
        external_refs = context.get('external_refs', [])
        usage_refs = context.get('usage_refs', [])

        report  = {
            'component': component_id,
            'status': "PASS",
            'issues': []
        }

        if not docstring or len(docstring.strip()) == 0:
            report['status'] = "FAIL"
            report['issues'].append("Docstring is missing or empty.")

        if 'TODO' in docstring or 'FIXME' in docstring:
            report['status'] = "WARNING"
            report['issues'].append("Docstring contains TODO or FIXME comments.")
        
        if '(' in source_code and ')' not in source_code:
            param_str = source_code.split('(')[1].split(')')[0]
            params = [p.strip() for p in param_str.split(',') if p.strip() and p != 'self']
            for param in params:
                if param not in docstring:
                    report['status'] = "WARNING"
                    report['issues'].append(f"Missing parameter descrpition: {param}")

        
        if self.llm_client:
            prompt = f"""Review this Python docstring for correctness and completeness.

            Source Code:
            {source_code}

            Dependencies:
            {dependencies}

            Usage:
            {usage_refs}

            External References:
            {external_refs}

            Docstring:
            {docstring}

            Provide a review summary with issues if any.
            """
            llm_response = self.llm_client.review_docstring(prompt)
            report['llm_review'] = llm_response

        return report