import pytest
from app.blender_connections import audit_connections
@pytest.mark.parametrize('x,status',[(1,'contact'),(1.1,'gap'),(.9,'penetration')])
def test_signed_connection_distinguishes_touch_gap_overlap(x,status):
 o={'a':{'location':[0,0,0],'dimensions':[1,1,1]},'b':{'location':[x,0,0],'dimensions':[1,1,1]}}
 q=audit_connections(o,[dict(a='a',b='b',axis=0,tolerance=1e-6)])['connections'][0];assert q['bounds_status']==status and q['exact_for_boxes']
def test_disjoint_other_axis_is_not_contact():
 o={'a':{'location':[0,0,0],'dimensions':[1,1,1]},'b':{'location':[1,4,0],'dimensions':[1,1,1]}}
 assert audit_connections(o,[dict(a='a',b='b',axis=0,tolerance=1e-6)])['connections'][0]['bounds_status']=='misaligned'
def test_unknown_object_rejected():
 with pytest.raises(ValueError):audit_connections({},[dict(a='a',b='b',axis=0,tolerance=0)])


def test_reversed_disjoint_is_not_penetration():
    objects={'a':{'location':[0,0,0],'dimensions':[1,1,1]},'b':{'location':[-2,0,0],'dimensions':[1,1,1]}}
    result=audit_connections(objects,[{'a':'a','b':'b','axis':0,'tolerance':1e-6}])['connections'][0]
    assert result['bounds_status']=='reversed_disjoint'
    assert result['aabb_overlap_volume_m3']==0

def test_reversed_touching_is_not_penetration():
    objects={'a':{'location':[0,0,0],'dimensions':[1,1,1]},'b':{'location':[-1,0,0],'dimensions':[1,1,1]}}
    result=audit_connections(objects,[{'a':'a','b':'b','axis':0,'tolerance':1e-6}])['connections'][0]
    assert result['bounds_status']=='reversed_contact'
    assert result['aabb_overlap_volume_m3']==0


def test_cpu_render_timeout_remains_bounded_and_build_limit_unchanged(tmp_path,monkeypatch):
    import subprocess
    from app.blender_backend import BlenderBackend
    seen=[]
    def run(command,**kwargs):
        seen.append(kwargs['timeout'])
        return subprocess.CompletedProcess(command,0,stdout='',stderr='')
    monkeypatch.setattr(subprocess,'run',run)
    for phase in ('render','build','reopen'):
        BlenderBackend._run(tmp_path,phase,['blender'])
    assert seen==[600,240,240]
