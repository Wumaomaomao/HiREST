import os
import json

def find_errors_json_files(root_dir):
	errors_files = []
	for dirpath, dirnames, filenames in os.walk(root_dir):
		for filename in filenames:
			if filename == "errors.json":
				errors_files.append(os.path.join(dirpath, filename))
	return errors_files

def load_all_errors(files):
	all_errors = []
	for file in files:
		try:
			with open(file, "r", encoding="utf-8") as f:
				data = json.load(f)
				if isinstance(data, list):
					all_errors.extend(data)
		except Exception as e:
			print(f"Failed to load {file}: {e}")
	return all_errors

def error_to_hashable(error):
	# Convert error dict to a hashable tuple for uniqueness
	# Sort keys for deterministic hashing
	if isinstance(error, dict):
		return tuple(sorted((k, json.dumps(v, sort_keys=True, ensure_ascii=False)) for k, v in error.items()))
	return str(error)

def main():
	bugs_dir = os.path.join(os.path.dirname(__file__), "..")
	bugs_dir = os.path.abspath(bugs_dir)
	errors_files = find_errors_json_files(bugs_dir)
	print(f"Found {len(errors_files)} errors.json files.")
	all_errors = load_all_errors(errors_files)
	print(f"Total error entries: {len(all_errors)}")
	unique_errors = set(error_to_hashable(e) for e in all_errors)
	print(f"Unique error entries: {len(unique_errors)}")

if __name__ == "__main__":
	main()
