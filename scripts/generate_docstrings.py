import os
import argparse
from navigator import build_dependency_graph
from agents.orchestrator import Orchestrator

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class LocalLLMClient:
    def __init__(self, model_name='TinyLlama/TinyLlama-1.1B-Chat-v1.0', device='cpu'):
        print(f"Loading model {model_name} on {device}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name).to(device)
        self.device = device

    def generate_docstring(self, prompt, max_new_tokens=200, temperature=0.7):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        return self.tokenizer.decode(output[0], skip_special_tokens=True).replace(prompt, '').strip()


def main(source_dir, output_dir):
    print(f"Building dependency graph from: {source_dir}")
    graph = build_dependency_graph(source_dir)
    print(f"Dependency graph built with {len(graph.nodes)} components.")

    llm_client = LocalLLMClient()

    if os.path.exists(output_dir):
        print(f"Output directory {output_dir} already exists. Removing it.")
        for root, dirs, files in os.walk(output_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    orchestrator = Orchestrator(graph, source_dir, output_dir, llm_client)
    orchestrator.run()
    print("Docstring generation complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate docstrings for Python codebase.")
    parser.add_argument("--source_dir", type=str, required=True, help="Path to source code directory")
    parser.add_argument("--output_dir", type=str, required=True, help="Path to output directory for annotated files")
    args = parser.parse_args()

    main(args.source_dir, args.output_dir)
