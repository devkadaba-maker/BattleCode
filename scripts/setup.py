#!/usr/bin/env python3
"""Install a reproducible competition environment with one command."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parents[1]
environment = ROOT / '.venv'
if not environment.exists():
    venv.EnvBuilder(with_pip=True).create(environment)
bindir = environment / ('Scripts' if os.name == 'nt' else 'bin')
python = bindir / ('python.exe' if os.name == 'nt' else 'python')
cli = bindir / ('unswbc.exe' if os.name == 'nt' else 'unswbc')
uv = shutil.which('uv')
if uv:
    subprocess.run([uv, 'pip', 'install', '--python', str(python), 'unswbc==1.2.9'], check=True)
else:
    if subprocess.run([str(python), '-m', 'pip', '--version'], stdout=subprocess.DEVNULL).returncode:
        subprocess.run([str(python), '-m', 'ensurepip'], check=True)
    subprocess.run([str(python), '-m', 'pip', 'install', 'unswbc==1.2.9'], check=True)
subprocess.run([str(cli), 'update', 'cpp_bot'], cwd=ROOT, check=True)
subprocess.run([str(cli)], cwd=ROOT, check=True)
print('Ready. The toolkit includes the judge engine and sandbox C++ compiler.')
