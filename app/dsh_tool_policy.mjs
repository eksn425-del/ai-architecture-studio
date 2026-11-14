// Model tool authorization, NOT process isolation. Fail closed for new native
// capabilities until reviewed. A trusted local process can still bypass this.
const readonly = new Set(['workspace_read','workspace_read_many','workspace_search',
  'kstudio_read_skill','sketchup_model_state','sketchup_view','sketchup_inspect_part','sketchup_inspect_owned_batch','sketchup_inspect_owned','sketchup_get_active_model_identity',
  'sketchup_get_model_info','sketchup_get_selection','sketchup_get_entities',
  'web_search','web_fetch','get_goal','list_agents','skill']);
const orchestration = new Set(['web_search','web_fetch','todo_write','exit_plan_mode',
  'get_goal','create_goal','update_goal','skill','send_message','interrupt_agent',
  'list_agents','subagent','subagent_fork']);
export function toolDenial(exec,{rootAgentId,hostNames,policy='production-file-proxy'}) {
  if (!exec.agent || !rootAgentId || exec.agent.id!==rootAgentId) {
    if (!readonly.has(exec.name)) return 'Auxiliary agents are read-only; return proposed changes to the root agent.';
  }
  // A second MCP is never a modeling writer, including trusted development.
  if (exec.name.startsWith('mcp__')) return 'External MCP tools are not reviewed project tools. Use the single owned-model host connector.';
  if (policy!=='trusted-development' && !hostNames.has(exec.name) && !orchestration.has(exec.name))
    return 'Unconfined native file/process tools are unavailable in this production profile. Use workspace_read/write/search and the approved ProjectRuby writer.';
  return null;
}
