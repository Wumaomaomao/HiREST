import json
import re

from hirest.llm.openai import OpenAIChatLLM


def retry(resp: str, op: int, max_retries=3):
    attempt = 0
    last_exception = None

    while attempt < max_retries:
        try:
            if op == 1:
                match = re.search(r'(\{.*\})', resp, re.DOTALL)
            else:
                match = re.search(r'(\[.*\])', resp, re.DOTALL)
            json_str = match.group(1)
            return json.loads(json_str)
        except Exception as e:
            print(f"\n\033[31m[offline][WARN] Attempt {attempt + 1} failed to parse JSON.\033[0m")
            last_exception = e

            fix_prompt = f"""
            The following JSON output is invalid. The error is:

            {str(e)}

            Please fix the JSON and return only the corrected JSON content.

            Invalid JSON:

            {resp}
            """.strip()

            fix_messages: list[dict[str, str]]  = [
                {
                    "role": "system",
                    "content": """
                        You are a helpful assistant that fixes invalid JSON.
                        
                        You need to repair the JSON data according to the following requirements:
                        
                        1. **Strictly** follow the JSON format to fix formatting issues, such as missing double quotes, commas, and parentheses.
                        
                        2. For JavaScript in the form of ".repeat()", you need to expand it into a complete expression, which is a string expression of a certain length. But the maximum length cannot exceed 100 characters, such as:
                        
                        If it appears "A".repeat(20), you need to replace it with "AAAAAAAAAAAAAAAAAAAA".
                    """},
                {"role": "user", "content": fix_prompt}
            ]

            resp = OpenAIChatLLM("gpt-4o").invoke(fix_messages)
            attempt += 1

    print("\n\033[31m[offline][ERROR] All retry attempts failed.\033[0m")
    print(f"\n\033[31m[offline][INFO] Last resp by LLM is:\033[0m\n{resp}")
    raise last_exception