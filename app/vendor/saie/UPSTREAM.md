# SAIE wall geometry subset

Repository: https://github.com/iamahsanmehmood/saie
Pinned commit: eff6f41ff866bef6b4f2b90be2faa6fe2cc4347f
Upstream path: ruby_plugin/su_mcp_bridge/ops/wall.rb
License: MIT; complete LICENSE retained.

Copied _read_centerline and _build_wall_group verbatim; enclosing namespace is KStudioSAIE. MM_TO_IN retained. Removed global model lookup, AI-ID upsert/delete, logging, tags and transaction code. K Studio's separate thin wrapper supplies only owned-root entities, validates explicit millimetre parameters, applies elevation and rejects duplicate names. This subset makes solid wall segments, not openings. It does not install the SAIE plugin or enable its MCP backend. Boolean opening code was intentionally not copied because upstream records reliability limits and it uses whole-model context.
