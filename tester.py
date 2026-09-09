import json
import copy
import os

output_dir = './test'
os.makedirs(output_dir, exist_ok=True)

with open('config.json') as f:
    original = json.load(f)


def save(data, filename):
    path = os.path.join(output_dir, filename)
    with open(path, 'w') as fh:
        json.dump(data, fh, indent=4)
        fh.write('\n')
    return path


created = []

# Category 1: Type mismatches and invalid data types
d = copy.deepcopy(original); d['lives'] = "three"
created.append(save(d, '01_config_lives_as_text.json'))

d = copy.deepcopy(original); d['screen_width'] = "large"
created.append(save(d, '02_config_screen_width_as_text.json'))

d = copy.deepcopy(original); d['points_per_ghost'] = "five-hundred"
created.append(save(d, '03_config_points_per_ghost_as_text.json'))

d = copy.deepcopy(original); d['seed'] = "random"
created.append(save(d, '04_config_seed_as_text.json'))

d = copy.deepcopy(original); d['highscore_filename'] = None
created.append(save(d, '05_config_highscore_filename_null.json'))

d = copy.deepcopy(original); d['lives'] = True
created.append(save(d, '06_config_lives_as_boolean.json'))

# Category 2: Invalid or extreme numeric values
d = copy.deepcopy(original); d['lives'] = -3
created.append(save(d, '07_config_lives_negative.json'))

d = copy.deepcopy(original); d['lives'] = 0
created.append(save(d, '08_config_lives_zero.json'))

d = copy.deepcopy(original); d['level_max_time'] = "-90"
created.append(save(d, '09_config_level_max_time_negative.json'))

d = copy.deepcopy(original); d['screen_width'] = 0
created.append(save(d, '10_config_screen_width_zero.json'))

d = copy.deepcopy(original); d['screen_height'] = -1080
created.append(save(d, '11_config_screen_height_negative.json'))

d = copy.deepcopy(original); d['points_per_pacgum'] = -10
created.append(save(d, '12_config_points_per_pacgum_negative.json'))

# Category 3: Altering the level array (edits applied to level1, the first entry)
d = copy.deepcopy(original); d['level_array_multiple_levels'] = []
created.append(save(d, '13_config_level_array_empty.json'))

d = copy.deepcopy(original); d['level_array_multiple_levels'][0]['width'] = -5
created.append(save(d, '14_config_level_width_negative.json'))

d = copy.deepcopy(original); d['level_array_multiple_levels'][0]['height'] = 0
created.append(save(d, '15_config_level_height_zero.json'))

d = copy.deepcopy(original); d['level_array_multiple_levels'][0]['width'] = "ten"
created.append(save(d, '16_config_level_width_as_text.json'))

d = copy.deepcopy(original); del d['level_array_multiple_levels'][0]['width']
created.append(save(d, '17_config_level_missing_width.json'))

d = copy.deepcopy(original); del d['level_array_multiple_levels'][0]['name']
created.append(save(d, '18_config_level_missing_name.json'))

# Category 4: Invalid highscore filename
d = copy.deepcopy(original); d['highscore_filename'] = ""
created.append(save(d, '19_config_highscore_filename_empty.json'))

d = copy.deepcopy(original); d['highscore_filename'] = "/sys/scores.json"
created.append(save(d, '20_config_highscore_filename_invalid_path.json'))

# Category 5: Missing keys or extra unknown fields
d = copy.deepcopy(original); del d['lives']
created.append(save(d, '21_config_lives_key_missing.json'))

d = copy.deepcopy(original); d['bonus_mode'] = True
created.append(save(d, '22_config_bonus_mode_unknown_key.json'))

# Category 6: JSON syntax errors (intentionally invalid JSON, on purpose)
base_text = json.dumps(original, indent=4) + '\n'

text = base_text.replace('"points_per_pacgum": 10,', '"points_per_pacgum": 10', 1)
assert text != base_text, "no match for missing-comma edit"
p = os.path.join(output_dir, '23_config_syntax_missing_comma.json')
with open(p, 'w') as fh:
    fh.write(text)
created.append(p)

val = original.get("screen_height", 1080)
text = base_text.replace(f'"screen_height": {val}', f'"screen_height": {val},', 1)
assert text != base_text, "no match for trailing-comma edit"
p = os.path.join(output_dir, '24_config_syntax_trailing_comma.json')
with open(p, 'w') as fh:
    fh.write(text)
created.append(p)

text = base_text.replace('"seed": "42"', 'seed: "42"', 1)
assert text != base_text, "no match for unquoted-key edit"
p = os.path.join(output_dir, '25_config_syntax_unquoted_key.json')
with open(p, 'w') as fh:
    fh.write(text)
created.append(p)

print(f"Created {len(created)} files\n")

# Validation pass: confirm the 22 "valid" variants parse, and the 3 syntax-error
# ones genuinely fail to parse (that's the point of those three).
syntax_error_files = {
    '23_config_syntax_missing_comma.json',
    '24_config_syntax_trailing_comma.json',
    '25_config_syntax_unquoted_key.json',
}

for path in created:
    name = os.path.basename(path)
    with open(path) as fh:
        content = fh.read()
    try:
        json.loads(content)
        status = "parses as valid JSON"
    except json.JSONDecodeError as e:
        status = f"fails to parse ({e.msg} at line {e.lineno})"
    expected_invalid = name in syntax_error_files
    ok = (expected_invalid and "fails" in status) or (not expected_invalid and "parses" in status)
    flag = "OK" if ok else "MISMATCH"
    print(f"[{flag}] {name}: {status}")
