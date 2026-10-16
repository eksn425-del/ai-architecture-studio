"""Explicit bounded Blender backend contract; not the SketchUp/Ruby writer."""
BOX={'type':'object','properties':{'name':{'type':'string'},'dimensions':{'type':'array','items':{'type':'number'},'minItems':3,'maxItems':3},'location':{'type':'array','items':{'type':'number'},'minItems':3,'maxItems':3}},'required':['name','dimensions','location'],'additionalProperties':False}
ASSEMBLY={'type':'object','properties':{'expected_geometry_sha256':{'type':'string'},'parts':{'type':'array','items':BOX,'minItems':1,'maxItems':64}},'required':['expected_geometry_sha256','parts'],'additionalProperties':False}
TOOLS=[{'name':name,'description':desc,'inputSchema':schema} for name,desc,schema in [
('blender_health','Read executable version',{'type':'object','properties':{},'additionalProperties':False}),
('blender_create_box','Legacy disposable single-box transport check',BOX),
('blender_create_assembly','Atomically create named box parts; preserve ALL existing meshes. Empty expected digest allowed only on blank scene.',ASSEMBLY),
('blender_edit_parts','Atomically resize/reposition only listed existing parts. Require current digest. KEEP every non-target object.',ASSEMBLY),
('blender_inspect','Read actual vertices, matrices, object identities, bounds and current digest after native reopen',{'type':'object','properties':{},'additionalProperties':False}),
('blender_render','CPU render oblique view; meshes unchanged',{'type':'object','properties':{},'additionalProperties':False}),
('blender_render_views','Render six canonical views with recorded camera settings; meshes unchanged',{'type':'object','properties':{},'additionalProperties':False})]]
ADAPTED_INSTRUCTIONS='''You are the supervised experimental Blender backend of K Studio.
This is an explicit backend adaptation, NOT the unchanged SketchUp/Ruby agent.
Preserve the product lifecycle: clarify -> plan -> execute -> inspect -> local edit -> review -> deliver.
Use only advertised bounded Blender tools. Coordinates are metres, X east, Y north, Z up.
No Ruby, .skp, arbitrary Python, original-project edits or claims of API autonomy.
Plan coherent named structural parts before writing. Read actual native geometry after writes.
For edits quote current geometry digest and list only intended parts; host preserves all other meshes.
After creation/edit request all six views, check the brief and distinguish geometric tests from visual/structural certification.
No image reconstruction quality claim is possible without supplied reference images.
The assistant supplies decisions through manually exchanged files; tool execution remains real K Studio parser/dispatch/MCP.
Be candid about missing capabilities and unfinished work. Do not report PASS for unexecuted steps.'''
