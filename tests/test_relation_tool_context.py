import json
import pytest
from app.relation_tool_context import prepare_relation_tools
from tests.test_repair_relations import scene,review,repairs

class Backend:
    current=scene()
    def dispatch(self,name,args):
        assert name=='blender_inspect_scene'
        return self.current

def test_budget_cannot_reset_by_model_but_new_host_approval_can_recover(tmp_path):
    backend=Backend();specs,call,before,after=prepare_relation_tools(tmp_path,backend)
    original=call('blender_plan_relation_repair',{'review':review(),'repairs':repairs()})
    backend.current=scene(1.08,2);after()
    backend.current=scene(1.04,3);blocked=after()
    assert blocked['status']=='blocked'
    with pytest.raises(ValueError):before({'objects':[backend.current['objects']['landing']]})
    retained=call('blender_plan_relation_repair',{'review':review(),'repairs':repairs()})
    assert retained['attempts']==2
    # Only a new host-confirmed plan changes the epoch; tool arguments cannot.
    (tmp_path/'runtime').mkdir(exist_ok=True)
    (tmp_path/'runtime/relation_execution_epoch.json').write_text(json.dumps({'pending_plan_id':'new-approved'}))
    fresh=call('blender_plan_relation_repair',{'review':review(),'repairs':repairs()})
    assert fresh['attempts']==0 and fresh['start_revision']==3
    assert 'repair_attempt_budget_exhausted' in (tmp_path/'runtime/relation_repair_history.jsonl').read_text()
    before({'objects':[backend.current['objects']['landing']]})


def test_unrelated_object_prevented_before_effect(tmp_path):
    backend=Backend();_,call,before,_=prepare_relation_tools(tmp_path,backend)
    call('blender_plan_relation_repair',{'review':review(),'repairs':repairs()})
    with pytest.raises(ValueError):before({'objects':[backend.current['objects']['wall']]})
