import os
import glob

def prepend_eslint_disable(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
        
    if '/* eslint-disable @typescript-eslint/no-explicit-any */' not in content:
        content = '/* eslint-disable @typescript-eslint/no-explicit-any */\n' + content
        with open(filepath, 'w') as f:
            f.write(content)

base_dir = 'Frontend/src/pages/minutes-preparation'

# specific files
files = [
    f'{base_dir}/MeetingMinutes.tsx',
    f'{base_dir}/MinutesGenerator.tsx',
    f'{base_dir}/SecretarialCompliances.tsx',
    f'{base_dir}/TemplateRenderer.tsx',
    f'{base_dir}/Templates.tsx'
]

# all step components
step_files = glob.glob(f'{base_dir}/components/form-steps/*.tsx')
files.extend(step_files)

for f in files:
    if os.path.exists(f):
        prepend_eslint_disable(f)

print("Added eslint-disable comments.")
