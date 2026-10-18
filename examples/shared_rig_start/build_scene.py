"""Minimal new-exercise starting point. This rest pose is not a finished exercise."""
import json
import sys
from pathlib import Path
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from shared_human import load_shared_human

# Start a new scene deliberately; the loader itself never clears your scene.
bpy.ops.wm.read_factory_settings(use_empty=True)
human = load_shared_human()

# Exercise-specific work belongs here:
# 1. Build equipment and solve motion using human.bones/human.rest.
# 2. Call human.apply(complete_armature_space_pose) for each frame.
# 3. Define reviewed primary/secondary muscle masks in bind-pose coordinates.
# 4. Run full-resolution garment, grip and equipment contact checks.
human.apply({name: matrix.copy() for name, matrix in human.rest.items()})

# Explicit preview opt-in; full-resolution rendering remains unchanged.
if '--preview-proxy' in sys.argv:
    from experiments.shared_proxy import create_shared_proxy
    proxy, proxy_report = create_shared_proxy(human)
    proxy.hide_set(False)
    human.h.hide_set(True)  # viewport only; high-resolution body still renders
    human.report['preview_proxy'] = proxy_report

out = Path(__file__).resolve().parent / 'output'
out.mkdir(exist_ok=True)
(out / 'shared_asset_validation.json').write_text(json.dumps(human.report, indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(out / 'shared_rig_start.blend'))
print('Shared muscular human ready; define exercise motion, equipment and muscles next.')
