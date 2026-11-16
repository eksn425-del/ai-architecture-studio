import math
import pytest
from app.blender_views import fitted_axis_camera
@pytest.mark.parametrize("view",["front","rear"])
@pytest.mark.parametrize("bounds", [[(-100,100),(-100,100),(0,250)],[(900,1100),(500,700),(0,250)]])
def test_oblique_preview_fits_large_and_translated_scene(view,bounds):
 p,c,s,clip=fitted_axis_camera(view,bounds)
 assert c==tuple((a+b)/2 for a,b in bounds)
 assert s>math.sqrt(sum((b-a)**2 for a,b in bounds))
 assert math.dist(p,c)>max(b-a for a,b in bounds)
 assert clip>math.dist(p,c)

@pytest.mark.parametrize("message",["先给方案不要建模。","先给我计划，确认后再执行。","先整理方案，暂不建模。"])
def test_requested_plan_with_deferred_build_remains_approvable(message):
 from app.models import AgentSession,ConversationRequest
 from app.reconstruction_runtime import resolve_reconstruction_action
 for action in ["auto","execute","plan"]:
  assert resolve_reconstruction_action(AgentSession(project_id="test",reconstruction_state="clarifying"),ConversationRequest(message=message,agent_action=action))=="plan"
