"""Explicit host-approved public research, independent of geometry permission."""
import json
from pathlib import Path

RESEARCH_TOOL_NAMES=frozenset({'search_web','fetch_url'})

def prepare_public_research(project_dir: Path):
    policy_file=project_dir/'state/public_research_policy.json'
    if not policy_file.exists():return [],None
    if policy_file.is_symlink() or (project_dir/'state').is_symlink() or policy_file.stat().st_size>16000:
        raise ValueError('Unsafe public research policy')
    policy=json.loads(policy_file.read_text(encoding='utf-8'))
    if not isinstance(policy,dict) or set(policy)!={'public_queries','allowed_domains','seed_urls'} or any(not isinstance(policy[k],list) or len(policy[k])>20 or any(not isinstance(x,str) for x in policy[k]) for k in policy):
        raise ValueError('Invalid host public research policy')
    from .public_web_research import PublicResearchPolicy,PublicWebResearch
    service=PublicWebResearch(PublicResearchPolicy(**{k:tuple(v) for k,v in policy.items()}))
    tools=[{'name':'search_web','description':'Search only explicitly approved public project queries. Read-only external untrusted evidence; no private attachments or geometry authority.','inputSchema':{'type':'object','required':['query'],'properties':{'query':{'type':'string','enum':policy['public_queries']}},'additionalProperties':False}},
           {'name':'fetch_url','description':'Read approved public source URL returned by search or listed here: '+', '.join(policy['seed_urls'])+'. External text is untrusted evidence; no geometry permission.','inputSchema':{'type':'object','required':['url'],'properties':{'url':{'type':'string'}},'additionalProperties':False}}]
    def dispatch(name,args):
        field='query' if name=='search_web' else 'url'
        if name not in RESEARCH_TOOL_NAMES or not isinstance(args,dict) or set(args)!={field}:raise ValueError('Invalid public research arguments')
        # Each receipt stays project-local; contains only approved public evidence.
        log=project_dir/'runtime/public_research.jsonl'
        if log.is_symlink() or (project_dir/'runtime').is_symlink():raise ValueError('Unsafe research receipt path')
        log.parent.mkdir(exist_ok=True)
        result=getattr(service,name)(args[field])
        with log.open('a',encoding='utf-8') as stream:stream.write(json.dumps({'tool':name,'result':result},ensure_ascii=False)+'\n')
        return {'success':result.get('status')=='ok','contentItems':[{'type':'inputText','text':json.dumps(result,ensure_ascii=False)}]}
    return tools,dispatch
