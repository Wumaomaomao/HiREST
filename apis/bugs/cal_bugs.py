#!/usr/bin/env python3
# coding: utf-8
import os
import re
import json
from pathlib import Path

def extract_fingerprint(resp_text):
	if not isinstance(resp_text, str):
		return ""
	# 1. stackTrace
	if 'stackTrace' in resp_text:
		start = resp_text.find('stackTrace')
		end = resp_text.find('java.lang.Thread', start)
		if end == -1:
			end = len(resp_text)
		frag = resp_text[start:end]
		thread_end = frag.find('Thread.java')
		if thread_end != -1:
			frag = frag[:thread_end]
		return frag.strip()
	# 2. <title>
	m = re.search(r'<title>(.*?)</title>', resp_text, re.IGNORECASE|re.DOTALL)
	if m:
		return m.group(1).strip()
	# 3. java: 行号
	java_lines = re.findall(r'(\w+\.java:\d+)', resp_text)
	if java_lines:
		return ','.join(sorted(set(java_lines)))
	# 4. Error: ...
	idx = resp_text.find('Error:')
	if idx != -1:
		frag = resp_text[idx:]
		# 去掉方括号、圆括号、引号里的内容
		frag = re.sub(r'\[.*?\]', '', frag)
		frag = re.sub(r'\(.*?\)', '', frag)
		frag = re.sub(r'".*?"', '', frag)
		frag = re.sub(r"'.*?'", '', frag)
		frag = re.sub(r'\s+', ' ', frag)
		return frag.strip()
	return resp_text[:120].strip()  # fallback: 截取前120字

def process_errors_json(errors_path):
	with open(errors_path, 'r', encoding='utf-8') as f:
		try:
			data = json.load(f)
		except Exception:
			return {}
	counter = {}
	for item in data:
		# item: [request, response]
		if isinstance(item, list) and len(item) == 2:
			resp = item[1]
			text = resp.get('text', '') if isinstance(resp, dict) else ''
			fp = extract_fingerprint(text)
			if fp:
				counter[fp] = counter.get(fp, 0) + 1
	return counter


def find_all_errors_json(base):
	"""递归查找所有 errors.json 文件"""
	for root, dirs, files in os.walk(base):
		for file in files:
			if file == 'errors.json':
				yield Path(root) / file

def main():
	base = Path(__file__).parent.resolve()
	for errors_path in find_all_errors_json(base):
		bugs = process_errors_json(errors_path)
		bugs_json_path = errors_path.parent / 'bugs.json'
		with open(bugs_json_path, 'w', encoding='utf-8') as f:
			json.dump(bugs, f, indent=2, ensure_ascii=False)
		print(f"[cal_bugs] {errors_path}: {len(bugs)} unique bugs, written to {bugs_json_path}")

if __name__ == '__main__':
	main()
