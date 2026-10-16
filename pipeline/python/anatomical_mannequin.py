"""Procedural approximate muscle volumes. NOT anatomically validated geometry.

This is an original low-poly visual proxy, not a reconstruction of any third-party media.
The 38 names count symmetric primitives; anatomy fidelity needs independent review.
"""
from __future__ import annotations

def generate_anatomical_muscle_primitives(joints):
    result=[]
    def point(name): return joints.get(name, (0.0,0.0,0.0))
    def add(name,a,b,r,tag,side=None,role='muscle'):
        if a not in joints or b not in joints: return
        result.append({'name':name,'p0':list(point(a)),'p1':list(point(b)),
                       'rad0':r,'rad1':r*.82,'muscle_tags':[tag], 'role':role})
    add('rectus_abdominis','pelvis','chest',.105,'rectus_abdominis')
    add('spinal_erectors','pelvis','chest',.085,'erector_spinae')
    add('sternum','spine','chest',.08,'pectoralis_major')
    add('neck','chest','head',.055,'trapezius')
    for s in ('L','R'):
        k=lambda x:f'{x}_{s}'
        specs=[
         ('pectoralis_major','chest',k('shoulder'),.105,'pectoralis_major'),
         ('anterior_deltoid',k('clavicle'),k('elbow'),.070,'anterior_deltoid'),
         ('lateral_deltoid',k('shoulder'),k('elbow'),.072,'deltoid'),
         ('posterior_deltoid',k('shoulder'),k('elbow'),.061,'posterior_deltoid'),
         ('biceps_brachii',k('shoulder'),k('elbow'),.06,'biceps_brachii'),
         ('triceps_brachii',k('shoulder'),k('elbow'),.062,'triceps_brachii'),
         ('brachialis',k('elbow'),k('wrist'),.043,'brachialis'),
         ('forearm_flexors',k('elbow'),k('wrist'),.047,'forearm_flexors'),
         ('forearm_extensors',k('elbow'),k('wrist'),.038,'forearm_extensors'),
         ('latissimus_dorsi','chest','pelvis',.092,'latissimus_dorsi'),
         ('external_obliques','spine',k('hip'),.085,'obliques'),
         ('gluteus_maximus',k('hip'),k('knee'),.105,'gluteus_maximus'),
         ('rectus_femoris',k('hip'),k('knee'),.075,'rectus_femoris'),
         ('vastus_lateralis',k('hip'),k('knee'),.091,'quadriceps'),
         ('hamstrings',k('hip'),k('knee'),.080,'hamstrings'),
         ('adductors',k('hip'),k('knee'),.067,'adductors'),
         ('gastrocnemius_calf',k('knee'),k('ankle'),.072,'gastrocnemius'),
        ]
        for name,a,b,r,tag in specs: add(f'{name}_{s}',a,b,r,tag)
    return result
