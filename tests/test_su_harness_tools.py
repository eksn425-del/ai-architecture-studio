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


def test_noncoplanar_polygon_is_blocked_and_box_uses_closed_faces():
    bad = {"parts":[{"name":"Panel","pieces":[
        {"kind":"polygon","vertices":[[0,0,0],[100,0,0],[100,100,2],[0,100,0]],"extrude":10}]}]}
    with pytest.raises(ValueError,match='coplanar'):
        compile_parts(bad)
    source = compile_parts(parts())
    box = source.split("when 'box'",1)[1].split("when 'polygon'",1)[0]
    assert 'child.manifold?' in box and 'pushpull' not in box

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


def window_bay(**changes):
    return {'parts': [{'name': 'FrontWall', 'pieces': [{
        'kind': 'window_bay', 'origin': [200, 100, 300], 'size': [3200, 250, 3300],
        'opening': [500, 800, 2200, 1650], 'frame_width_mm': 60,
        'frame_depth_mm': 95, 'recess_mm': 75, **changes,
    }]}]}


def test_window_bay_routes_one_verified_definition_to_the_guarded_writer():
    args = window_bay(repeat=3, rotation_deg=90, step=[0, 3200, 0], glass_thickness_mm=12)
    source = compile_parts(args)
    assert 'child = build_window_bay.call(group, piece, name)' in source
    assert 'add_instance(child.definition' in source
    assert 'instance.definition.persistent_id != child.definition.persistent_id' in source
    assert 'frame_width_mm' in source
    assert validate_project_ruby_source('harness_building', source) == source
    assert 'window_bay' in next(s['description'] for s in tool_specs() if s['name'] == 'sketchup_apply_parts')


def test_window_bay_measurement_is_an_optional_owned_inspection(tmp_path, monkeypatch):
    from types import SimpleNamespace
    from app.su_harness_tools import SUHarnessTools

    observed = []
    executor = SimpleNamespace(verify_active_model=lambda: {}, ruby_state={},
                               inspect_owned=lambda args: observed.append(args) or {'success': True})
    monkeypatch.setattr('app.su_harness_tools.ProjectRubyExecutor', lambda *_, **__: executor)
    surface = SUHarnessTools(tmp_path, None).prepare(project_dir=tmp_path, mcp_enabled=True,
                                                     model_path=tmp_path / 'copy.skp', model_guid='g', stage_scoped=True)
    path = ['FrontWall', 'piece_0']
    assert surface.dispatch('sketchup_inspect_part', {'path': path, 'window_bay': True})['success']
    assert observed == [{'script_id': 'harness_building', 'path': path, 'limit': 100, 'window_bay': True}]


@pytest.mark.parametrize('change', [
    {'opening': [500, 0, 2200, 1650]}, {'opening': [500, 800, 2700, 1650]},
    {'opening': [-5, 800, 2200, 1650]}, {'opening': [500, 800, 2200, 0]},
    {'frame_width_mm': 900}, {'frame_depth_mm': 200}, {'glass_thickness_mm': 100},
    {'glass_alpha': -0.1}, {'frame_color': [20, 256, 20]}, {'alpha': 0.7},
    {'repeat': 3, 'rotation_deg': 90, 'step': [0, 3199, 0]},
    {'repeat': 2}, {'ruby': 'puts 1'},
])
def test_window_bay_rejects_bad_construction_before_sketchup(change):
    with pytest.raises(ValueError):
        compile_parts(window_bay(**change))


def test_window_bay_definition_limit_matches_native_method_ledger():
    args = window_bay()
    args['parts'][0]['pieces'] *= 129
    with pytest.raises(ValueError, match='method ledger'):
        compile_parts(args)


def straight_stair(**changes):
    return {'parts': [{'name': 'EastStair', 'pieces': [{
        'kind': 'stair_flight', 'origin': [1000, 2000, 100], 'top_z_mm': 3200,
        'width_mm': 1350, 'risers': 18, 'going_mm': 265, 'flight_thickness_mm': 170,
        'landing_depth_mm': 1400, 'landing_thickness_mm': 230, **changes,
    }]}]}


def test_straight_flight_and_landing_use_one_level_and_full_width_bearing_face():
    args = straight_stair()
    presets = validate_parts(args)[0]['pieces'][0]['stair_profiles']
    near, far = presets['Flight']
    landing_low, landing_high = presets['UpperLanding']
    rise = 3100 / 18
    assert [point[2] for point in near[1:-1:2]] == pytest.approx([100 + i * rise for i in range(1, 18)])
    assert near[-2] == pytest.approx([5505, 2000, 3200 - rise])
    assert far[-2] == pytest.approx([5505, 3350, 3200 - rise])
    assert all(point[2] == 3200 for point in landing_high)
    assert (landing_low[0], landing_low[-1]) == ([5505, 2000, 2970], [5505, 3350, 2970])
    assert near[-1][2] < landing_low[0][2] < near[-2][2]
    assert 'stair_profiles' not in args['parts'][0]['pieces'][0]
    source = compile_parts(args)
    stair_source = source.split("when 'stair_flight'", 1)[1]
    assert 'solid.manifold?' in stair_source and 'pushpull' not in stair_source
    assert validate_project_ruby_source('harness_building', source) == source


@pytest.mark.parametrize('change', [
    {'risers': 1}, {'risers': 18.0}, {'risers': 33}, {'top_z_mm': 110},
    {'landing_thickness_mm': 170}, {'going_mm': 10000}, {'width_mm': 0},
    {'repeat': 2}, {'stair_profiles': []},
])
def test_straight_flight_rejects_invalid_or_untrusted_geometry(change):
    with pytest.raises(ValueError):
        compile_parts(straight_stair(**change))
