import pytest
from app.project_ruby import validate_project_ruby_source
from app.litellm_runtime import _current_visual_context

@pytest.mark.parametrize('origin',['10,8,0','10,0,0','0,8,0','-10, .5, 0'])
def test_metric_script_rejects_raw_inch_wall_origin(origin):
    with pytest.raises(ValueError, match='Mixed-unit Point3d'):
        validate_project_ruby_source('villa',f'width = 10.m\np = Geom::Point3d.new({origin})')

@pytest.mark.parametrize('source',[
    'width = 10.m\np = Geom::Point3d.new(10.m,8.m,0)',
    'width = 10.m\np = Geom::Point3d.new(0,0,0)',
    'width = 10.m\np = Geom::Point3d.new(10.inch,8.inch,0)',
    'width = 120\np = Geom::Point3d.new(10,8,0)',
    '# width = 10.m\np = Geom::Point3d.new(10,8,0)',
])
def test_explicit_units_zero_origin_and_inch_only_scripts_remain_valid(source):
    assert validate_project_ruby_source('villa',source)==source


def test_old_large_tool_dumps_bounded_without_breaking_exchanges_or_audit():
    messages=[{'role':'system','content':'method'}, {'role':'user','content':'confirmed dimensions'}]
    for i in range(12):
        messages.extend([
            {'role':'assistant','tool_calls':[{'id':str(i),'type':'function','function':{'name':'workspace_read','arguments':'{}'}}],'content':None},
            {'role':'tool','tool_call_id':str(i),'content':str(i)+'x'*20000},
        ])
    active=_current_visual_context(messages)
    assert len(active)==len(messages)
    assert active[:2]==messages[:2]
    assert all(a.get('tool_call_id')==b.get('tool_call_id') for a,b in zip(active,messages))
    assert active[-12:]==messages[-12:]
    assert len(active[3]['content'])<4500
    assert len(messages[3]['content'])>20000  # full audit is not mutated
    assert sum(len(m.get('content') or '') for m in active)<170000


def test_existing_root_requires_deliberate_rebuild_before_any_model_call():
    from app.project_ruby import ProjectRubyExecutor
    executor=object.__new__(ProjectRubyExecutor)
    executor.ruby_state={'villa':{'root_pid':123,'revision':2}}
    with pytest.raises(ValueError,match='unrelated object IDs'):
        executor.run({'script_id':'villa','ruby_source':'root.name = "Villa"'})
