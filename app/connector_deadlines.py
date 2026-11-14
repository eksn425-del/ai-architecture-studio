"""One bounded response window on both sides of the native transport."""


def native_response_timeout(name):
    return {'sketchup_eval_project_file':120, 'sketchup_export_view_image':30}.get(name,12)
