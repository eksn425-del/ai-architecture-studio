import pytest
from scripts.audit_architecture_contacts import triangle_distance,measure
from scripts.audit_architecture_contacts import stair_terminals


def test_interior_crossing_is_detected_even_without_shared_vertices():
    a=[[0,0,0],[10,0,0],[0,10,0]]
    b=[[2,2,-5],[2,2,5],[3,3,5]]
    assert triangle_distance(a,b)==0


def test_parallel_gap_and_coplanar_overlap():
    a=[[0,0,0],[10,0,0],[0,10,0]]
    b=[[1,1,3],[2,1,3],[1,2,3]]
    assert triangle_distance(a,b)==pytest.approx(3)
    assert triangle_distance(a,[[x,y,0] for x,y,z in b])==0


def test_missing_group_never_passes_and_corner_contact_is_not_seam_pass():
    assert measure([],['flight'],['landing'])['status']=='MISSING_GEOMETRY'
    f=[{'path':['flight'],'pid':1,'triangles_mm':[[[0,0,0],[1,0,0],[0,1,0]]]},
       {'path':['landing'],'pid':2,'triangles_mm':[[[1,0,0],[2,0,0],[1,-1,0]]]}]
    result=measure(f,['flight'],['landing'])
    assert result['status']=='CONTACT_OR_INTERSECTION'
    assert 'full-width seam' in result['limitation']


def test_contact_at_bottom_does_not_hide_disconnected_top():
    data={'collector':'KStudioNativeArchitectureFeatures/1','root_pid':19,
          'owned_identity':{'revision':11},'root_geometry_material_sha256':'fixture',
          'faces':[{'path':['flight'],'pid':1,'triangles_mm':[[[0,0,0],[1,0,0],[0,1,0]],[[0,0,600],[1,0,600],[0,1,600]]]},
                   {'path':['landing'],'pid':2,'triangles_mm':[[[0,0,0],[1,0,0],[0,1,0]]]}]}
    assert measure(data['faces'],['flight'],['landing'])['minimum_surface_distance_mm']==0
    result=stair_terminals(data,[(['flight'],['landing'])])
    assert result['contacts'][0]['minimum_surface_distance_mm']==600
