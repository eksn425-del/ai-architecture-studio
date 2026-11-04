"""Generate only synthetic local request fixtures into an explicit output directory."""
import argparse
import json
from pathlib import Path
from PIL import Image
from app.dsh_configuration import resolve_configuration
from app.dsh_images import image_block
from app.dsh_full_profile import provider_retry_policy


def prepare(root):
    root=Path(root);root.mkdir(parents=True,exist_ok=True)
    images=[]
    for i,(fmt,suffix) in enumerate([('PNG','png'),('JPEG','jpg'),('WEBP','webp'),('GIF','gif')]):
        path=root/f'source.{suffix}'
        Image.new('RGB',(12,8),('red','green','blue','yellow')[i]).save(path,format=fmt)
        block,_=image_block(path);images.append({'id':f'image{i}',**block})
    models={effort:resolve_configuration({'api_base':'https://example.invalid','model':'fixture-model',
        'mode':'compatible','reasoning_effort':effort,'capabilities_json':json.dumps({'vision':True})}).model_descriptor()
        for effort in ('provider-default','low','high')}
    (root/'configuration.json').write_text(json.dumps({'models':models,'images':images}),encoding='utf-8')
    (root/'retry-policy.json').write_text(json.dumps(provider_retry_policy()),encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output_dir');prepare(parser.parse_args().output_dir)
