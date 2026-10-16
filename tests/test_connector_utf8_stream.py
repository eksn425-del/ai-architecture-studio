import json
import shutil
import subprocess

import pytest

from scripts.patch_connector_utf8_stream import patch_bytes, apply_patch


def original(eol=b'\n'):
    return eol.join([b'const socket = net.createConnection({host,port});', b'    socket.on("data", (chunk) => {', b'      response += chunk.toString("utf8");', b'    });'])


@pytest.mark.parametrize('eol', [b'\n', b'\r\n'])
def test_patch_is_exact_idempotent_and_preserves_other_connector_bytes(tmp_path, eol):
    path = tmp_path / 'connector.mjs'; data = original(eol); path.write_bytes(data)
    result = apply_patch(path)
    assert result['status'] == 'PATCHED' and not result['credentials_or_auth_changed']
    assert path.read_bytes() == patch_bytes(data)
    assert (tmp_path / result['backup']).read_bytes() == data
    assert apply_patch(path)['status'] == 'ALREADY_PATCHED'
    assert path.read_bytes().count(b'socket.setEncoding("utf8")') == 1
    with pytest.raises(ValueError):
        patch_bytes(data + data)


def test_partial_utf8_bytes_round_trip_without_replacement_characters():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node runtime unavailable')
    # Readable stream decoding is the same implementation used by net.Socket;
    # one-byte chunks make the otherwise timing-dependent failure deterministic.
    source = r'''
const {PassThrough} = require('node:stream');
const crypto = require('node:crypto');
const text = JSON.stringify({name:'组“633”#2',note:'原八张建筑整图'});
const old = new PassThrough(); const fixed = new PassThrough();
let broken='', correct='';
old.on('data',x=>broken+=x.toString('utf8'));
fixed.setEncoding('utf8'); fixed.on('data',x=>correct+=x);
for(const byte of Buffer.from(text,'utf8')) { old.write(Buffer.from([byte])); fixed.write(Buffer.from([byte])); }
old.end(); fixed.end();
const sha=x=>crypto.createHash('sha256').update(x,'utf8').digest('hex');
process.stdout.write(JSON.stringify({broken:broken!==text,correct:correct===text,sha_match:sha(correct)===sha(text),replacement:correct.includes('\uFFFD')}));
'''
    run = subprocess.run([node, '-e', source], check=True, capture_output=True, encoding='utf-8')
    result = json.loads(run.stdout)
    assert result == {'broken': True, 'correct': True, 'sha_match': True, 'replacement': False}
