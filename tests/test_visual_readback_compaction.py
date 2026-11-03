"""Internal render messages must not replace the current human instruction."""
import copy
import pytest
from app.context_compaction import _current_real_user_index, compact_active_reconstruction_context


def transcript(prefix):
    rows=[{'role':'system','content':'host rules'}, {'role':'user','content':'Keep the roof; edit only the entrance.'}]
    for i in range(3):
        rows.extend([{'role':'assistant','tool_calls':[{'id':str(i),'type':'function','function':{'name':'inspect','arguments':'{}'}}]},
                     {'role':'tool','tool_call_id':str(i),'content':'x'*5000}])
    rows.append({'role':'user','content':[{'type':'text','text':prefix},
                                       {'type':'image_url','image_url':{'url':'data:image/png;base64,fixture'}}]})
    return rows

@pytest.mark.parametrize('prefix', ['Visual readback from tool blender_render_scene.',
                                    'Visual readback from tool sketchup_capture_view.',
                                    'Visual readback from SketchUp tool sketchup_capture_view.'])
def test_render_is_internal_and_latest_two_exchanges_survive(prefix):
    rows=transcript(prefix);original=copy.deepcopy(rows)
    assert _current_real_user_index(rows)==1
    compacted,stats=compact_active_reconstruction_context(rows,'CURRENT VERIFIED CHECKPOINT',threshold_chars=1,compact_current_turn=True)
    assert stats['compacted']
    assert [r['tool_call_id'] for r in compacted if r['role']=='tool']==['1','2']
    assert rows[1] in compacted and rows[-1] in compacted
    assert rows==original

def test_true_new_user_after_render_is_not_mistaken_for_internal():
    rows=transcript('Visual readback from tool blender_render_scene.')
    rows.append({'role':'user','content':'Stop the edit; inspect only.'})
    assert _current_real_user_index(rows)==len(rows)-1
    compacted,_=compact_active_reconstruction_context(rows,'CHECKPOINT',threshold_chars=1,compact_current_turn=True)
    assert rows[-1] in compacted

def test_new_readback_cannot_hide_unresolved_tool_exchange():
    rows=transcript('Visual readback from tool blender_render_scene.')
    rows.pop(7)  # last writer result is absent; do not hide uncertain effect.
    compacted,stats=compact_active_reconstruction_context(rows,'CHECKPOINT',threshold_chars=1,compact_current_turn=True)
    assert not stats['compacted'] and compacted==rows
