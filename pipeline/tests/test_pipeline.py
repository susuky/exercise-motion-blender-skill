import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'python'))
from validate_motion_spec import validate_full
from interpolate_motion import expand_motion_spec
from equipment_registry import get_equipment_archetype,normalize_equipment_type
class TestPipeline(unittest.TestCase):
 def test_three_samples_validate(self):
  for p in (ROOT/'samples').glob('*.motion_spec.json'):
   with self.subTest(p=p.name):self.assertEqual(validate_full(str(p))['status'],'PASS')
 def test_expansion(self):
  exp=expand_motion_spec(str(ROOT/'samples'/'dumbbell_lateral_raise.motion_spec.json'))
  self.assertEqual(len(exp['skeleton_frames']),exp['total_frames'])
  self.assertTrue(exp['skeleton_frames'][0]['joints_3d'])
 def test_rejects_invalid_spec(self):
  spec=json.loads((ROOT/'samples'/'dumbbell_lateral_raise.motion_spec.json').read_text())
  spec['phases'][0]['start_t']=0.4
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'invalid.json';p.write_text(json.dumps(spec))
   self.assertNotEqual(validate_full(str(p))['status'],'PASS')
 def test_taxonomy(self):
  self.assertEqual(normalize_equipment_type('Body Weight'),'body_weight')
  self.assertEqual(get_equipment_archetype('barbell'),'rigid_bilateral_bar')
  self.assertEqual(get_equipment_archetype('not_real'),'unknown')
if __name__=='__main__':unittest.main()
