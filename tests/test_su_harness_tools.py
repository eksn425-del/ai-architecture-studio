import pytest
from app.su_harness_tools import compile_parts, validate_parts, tool_specs
from app.project_ruby import validate_project_ruby_source
from app.native_execution_safety import validate_host_tools


def parts(**kwargs):
    return {"parts":[{"name":"Roof", "pieces":[{"kind":"box","origin":[0,0,0],"size":[100,200,30],**kwargs}]}]}


@pytest.mark.parametrize("value", [float("nan"),float("inf"),True,"100",100001])
def test_reject_nonfinite_or_code_dimensions(value):
    with pytest.raises(ValueError): validate_parts(parts(size=[value,20,30]))


def test_only_typed_data_no_code_or_host_paths():
    for bad in [parts(code="puts 1"), {**parts(),"script_path":"evil.rb"},parts(repeat=100,step=[100000,0,0])]:
        with pytest.raises(ValueError): validate_parts(bad)
    bad=parts();bad["parts"][0]["name"]='#{File.read("secret")}'
    with pytest.raises(ValueError):validate_parts(bad)


def test_compiler_reuses_guarded_executor_and_keeps_part_identity():
    source=compile_parts(parts(repeat=3,step=[1000,0,0]))
    assert validate_project_ruby_source("harness_building",source)==source
    assert "clear_owned_contents.call" in source
    assert "remove_owned_group.call" not in source
    assert "add_instance" in source
    validate_host_tools(tool_specs())
    with pytest.raises(ValueError):validate_host_tools([{"name":"sketchup_run_project_ruby"}])


def test_identical_names_and_resource_bounds_rejected():
    p=parts();p["parts"]*=2
    with pytest.raises(ValueError):validate_parts(p)
    with pytest.raises(ValueError):validate_parts(parts(repeat=101))


def test_supported_facade_polygon_and_cylinder():
    for piece in [{"kind":"polygon","vertices":[[0,0,0],[20,0,0],[20,10,0]],"extrude":10},
                  {"kind":"cylinder","origin":[0,0,0],"radius":20,"height":100}]:
        source=compile_parts({"parts":[{"name":"Part", "pieces":[piece]}]})
        validate_project_ruby_source("harness_building",source)


def curved_profile():
    return {'parts':[{'name':'Balcony','pieces':[{'kind':'profile','segments':[
        [[0,0,0],[0,100,0],[100,100,0],[100,0,0]],
        [[100,0,0],[100,-100,0],[0,-100,0],[0,0,0]]],
        'extrude':20,'smooth':True}]}]}


def test_curve_sampling_is_bounded_closed_planar_and_preserves_input():
    from app.su_harness_tools import profile_vertices
    p=curved_profile(); points=profile_vertices(p['parts'][0]['pieces'][0])
    assert len(points)==16 and points[0]==[0,0,0] and points[8]==[100,0,0]
    assert max(v[1] for v in points)==75 and min(v[1] for v in points)==-75
    source=compile_parts(p)
    assert p['parts'][0]['pieces'][0]['kind']=='profile'
    validate_project_ruby_source('harness_building',source)


@pytest.mark.parametrize('bad',['gap','nonplanar','oversize','code','smooth'])
def test_curves_reject_invalid_geometry_before_native_execution(bad):
    p=curved_profile(); piece=p['parts'][0]['pieces'][0]
    if bad=='gap':piece['segments'][1][-1]=[1,0,0]
    if bad=='nonplanar':piece['segments'][0][1][2]=20
    if bad=='oversize':piece['samples']=200
    if bad=='code':piece['source']='File.read'
    if bad=='smooth':piece['smooth']='yes'
    with pytest.raises(ValueError):compile_parts(p)
