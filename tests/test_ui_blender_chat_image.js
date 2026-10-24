// Exercise the production renderer with the actual bundled Markdown parser.
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const markdownit = require('../app/static/vendor/markdown-it/markdown-it.min.js');
const source = fs.readFileSync(path.join(__dirname, '../app/static/studio.js'), 'utf8');
function production(name) {
  const at = source.search(new RegExp('^function ' + name + '\\(', 'm'));
  assert.notEqual(at, -1);
  return source.slice(at, source.indexOf('\n}', at) + 2);
}
const context = vm.createContext({window:{markdownit}, state:{projectId:'test & fixture'}});
vm.runInContext(['chatText','projectFileUrl','escapeHtml'].map(production).join('\n'), context);
const view = 'runtime/blender/' + 'a'.repeat(32) + '/view-front_elevation.png';

test('current Blender screenshot appears in chat through the current project file route', () => {
  const html = context.chatText(`![Current view](${view})`);
  assert.match(html, /<img /);
  assert.ok(html.includes('/api/projects/test%20%26%20fixture/files/' + view));
  assert.match(html, /alt="Current view"/);
  assert.doesNotMatch(html, /src="runtime/);
});

for (const src of [
  'https://untrusted.example/view.png',
  'runtime/blender/not-a-model/view-front.png',
  'runtime/blender/' + 'a'.repeat(32) + '/../private.png',
  'runtime/blender/' + 'a'.repeat(32) + '/view-front.png?token=secret',
  'runtime/blender/' + 'a'.repeat(32) + '/model.blend',
  '/api/projects/another/files/' + view,
]) {
  test('does not embed an unapproved image source: ' + src, () => {
    assert.doesNotMatch(context.chatText(`![Untrusted view](${src})`), /<img |<a /);
  });
}

test('existing workspace image rendering remains available and HTML is escaped', () => {
  assert.match(context.chatText('![Sketch](notes/sketch.png)'), /<img /);
  assert.doesNotMatch(context.chatText('<img src=x onerror=alert(1)>'), /<img /);
});
