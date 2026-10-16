import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'python'))
from validate_motion_spec import validate_full
from interpolate_motion import expand_motion_spec
from equipment_registry import get_equipment_archetype,normalize_equipment_type
from anatomical_mannequin import generate_anatomical_muscle_primitives
from run_pipeline import run
class TestPipeline(unittest.TestCase):
 def test_three_samples_validate(self):
  for p in (ROOT/'samples').glob('*.motion_spec.json'):
   with self.subTest(p=p.name):self.assertEqual(validate_full(str(p))['status'],'PASS')
 def test_core_export(self):
  p=ROOT/'samples'/'dumbbell_lateral_raise.motion_spec.json'
  with tempfile.TemporaryDirectory() as d:
   result=run(p,Path(d),render=False)
   self.assertEqual(result['status'],'PASS',result.get('error'))
   for key in ('bvh','gltf','expanded'):self.assertTrue(Path(result['generated'][key]).is_file())
 def test_rejects_invalid_spec_without_export(self):
  spec=json.loads((ROOT/'samples'/'dumbbell_lateral_raise.motion_spec.json').read_text())
  spec['phases'][0]['start_t']=0.4
  with tempfile.TemporaryDirectory() as d:
   s=Path(d)/'invalid.motion_spec.json';s.write_text(json.dumps(spec))
   result=run(s,Path(d)/'out',render=False)
   self.assertEqual(result['status'],'INVALID_SPEC')
   self.assertNotIn('expanded',result['generated'])
 def test_taxonomy(self):
  self.assertEqual(normalize_equipment_type('Body Weight'),'body_weight')
  self.assertEqual(get_equipment_archetype('barbell'),'rigid_bilateral_bar')
  self.assertEqual(get_equipment_archetype('not_real'),'unknown')
 def test_proxy_primitives(self):
  exp=expand_motion_spec(str(ROOT/'samples'/'dumbbell_lateral_raise.motion_spec.json'))
  prims=generate_anatomical_muscle_primitives(exp['skeleton_frames'][0]['joints_3d'])
  self.assertEqual(len(prims),38)
  self.assertTrue(all(p['rad0']>0 for p in prims))
if __name__=='__main__':unittest.main()
