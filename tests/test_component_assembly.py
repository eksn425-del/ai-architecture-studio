from app.component_assembly import native_component_diagnostics


def test_native_named_dimensions_are_not_joint_or_visual_pass():
    row={'name':'WALL','persistent_id':12,'bounds_mm':{'size':[1000,200,3000]},'locked':False}
    result=native_component_diagnostics({'objects':[row]})
    assert result['named_native_group_checks']=='PASS'
    assert result['status']=='PARTIAL'
    assert result['roof_wall_window_stair_joint_quality']=='NOT_VERIFIED_BY_NAMES_OR_BOUNDS'


def test_no_anonymous_or_duplicate_assemblies():
    row={'name':'','persistent_id':0,'bounds_mm':{'size':[1,-1,3]}}
    assert native_component_diagnostics({'objects':[row,row]})['status']=='FAIL'
