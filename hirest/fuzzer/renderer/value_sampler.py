import json
import logging
import re

from typing import Any

from hirest.llm.openai import OpenAIChatLLM
from hirest.model.sisp import SISP_SS

logger = logging.getLogger(__name__)


def _build_prompt(sisp_ss: SISP_SS, format: str, k: int) -> str:
	seeds = json.dumps(list(sisp_ss.samples or []), ensure_ascii=False)
	return f"""
Generate diverse test values for ONE API parameter subspace.

Input:
- parameter_name: {sisp_ss.param_name}
- format: {format}
- category: {sisp_ss.category}
- description: {sisp_ss.description}
- current_representative_samples: {seeds}
- expected_count: {k}

Rules:
1. Return ONLY a JSON array.
2. The array length should be <= expected_count.
3. Keep values consistent with the format, category and description.
4. Avoid duplicates of current_representative_samples.
5. Do not output markdown, comments, or explanation.

Note:
You MUST generate the values strictly following the above rules. If you cannot generate any new value, return an EMPTY JSON array.

Output example:
["v1", "v2", "v3"]
""".strip()


def _parse_json_list(text: str) -> list[Any]:
	try:
		data = json.loads(text)
		return data if isinstance(data, list) else []
	except Exception:
		match = re.search(r"(\[.*\])", text, re.DOTALL)
		if not match:
			return []
		try:
			data = json.loads(match.group(1))
			return data if isinstance(data, list) else []
		except Exception:
			return []


def _dedupe_keep_order(values: list[Any]) -> list[Any]:
	result: list[Any] = []
	seen: set[str] = set()
	for item in values:
		key = repr(item)
		if key in seen:
			continue
		seen.add(key)
		result.append(item)
	return result


def sample_more_values(sisp_ss: SISP_SS, format:str, k: int = 8, model: str = "gpt-5") -> list[Any]:
	"""Generate more values from a SISP_SS via a simple LLM prompt.

	Merge generated values into sisp_ss.samples and return only newly added values.
	"""
	if k <= 0:
		return []

	if sisp_ss.category == "<MISS_KEY>":
		if "<MISS_KEY>" not in (sisp_ss.samples or []):
			sisp_ss.samples = list(sisp_ss.samples or []) + ["<MISS_KEY>"]
		return []

	seeds = list(sisp_ss.samples or [])
	if not seeds:
		return []

	prompt = _build_prompt(sisp_ss, format, k)
	messages: list[dict[str, str]] = [
		{
			"role": "system",
			"content": "You are a test-value generator. Output strictly JSON array only.",
		},
		{
			"role": "user",
			"content": prompt,
		},
	]

	try:
		resp = OpenAIChatLLM(model).invoke(messages)
		llm_values = _parse_json_list(resp)
	except Exception as exc:
		logger.warning("LLM sampling failed for %s: %s", sisp_ss.param_name, exc)
		llm_values = []

	# Keep only values that are truly new to current samples.
	seed_keys = {repr(v) for v in seeds}
	new_values: list[Any] = []
	for item in _dedupe_keep_order(llm_values):
		if repr(item) in seed_keys:
			continue
		new_values.append(item)
		if len(new_values) >= k:
			break

	# Merge new values back into sisp_ss.samples.
	if new_values:
		sisp_ss.samples = _dedupe_keep_order(seeds + new_values)

	return new_values
