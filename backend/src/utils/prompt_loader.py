# src/utils/prompt_loader.py
"""
PromptLoader:
Loads and lists prompt text files from a specified directory for LLM agents.
Provides a simple API for accessing prompt content.
"""

from json import load
from os import listdir, path
from typing import List


class PromptLoader:
    """
    Utility class to load and list prompt files from a directory.
    """

    def __init__(self, base_path: str = "prompts"):
        """
        Args:
            base_path (str): Directory containing prompt files.
        """
        self.base_path = base_path

    def load_prompt(self, prompt_name: str, is_json: bool = False):
        """
        Load a prompt from a file (text or JSON).

        Args:
            prompt_name (str): Name of the prompt file (without extension).
            is_json (bool): If True, load as JSON; otherwise as text.

        Returns:
            str or dict: Content of the prompt file (str for .txt, dict for .json).

        Raises:
            FileNotFoundError: If the prompt file does not exist.
            ValueError: If the JSON is invalid when is_json=True.
        """
        extension_name = "json" if is_json else "txt"
        prompt_path = path.join(self.base_path, f"{prompt_name}.{extension_name}")
        with open(prompt_path, "r", encoding="utf-8") as f:
            return load(f) if is_json else f.read()

    def list_prompts(self) -> List[str]:
        """
        List all available prompt files (without extension) in the base directory.

        Returns:
            List[str]: List of prompt file names (without extension).
        """
        if not path.isdir(self.base_path):
            return []
        return [
            path.splitext(fname)[0]
            for fname in listdir(self.base_path)
            if fname.endswith(".txt")
        ]
