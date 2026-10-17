# Actual Windows approval failure

Three real browser requests returned HTTP 500: initial formal-plan preparation, one identical retry after a normal refresh, then explicit planning-only input. These failures occur before app-server/model/tool dispatch, so they do not appear as failed modeling tools or persisted conversation turns.

Sanitized stack excerpt (same last frames on all three failures):

```text
app/main.py:1572 converse -> converse_turn(project_id, request)
app/main.py:1683 converse_turn -> capture_pending_design_plan(project_dir, "", is_followup=False)
app/design_scope_approval.py:77 -> current_reference_fingerprint(project_dir)
app/design_scope_approval.py:32 -> json.loads(context_path.read_text())
pathlib.py:1028 -> f.read()
UnicodeDecodeError: 'gbk' codec can't decode byte 0xae in position 49: illegal multibyte sequence
```

The JSON is UTF-8, includes the Chinese project name and image-reference fields, and is readable when inspected explicitly as UTF-8. The actual Python is 3.12.2 with locale encoding cp936, despite the executable directory being named python3.10.4. The child process uses the established launcher profile and PYTHONIOENCODING=utf-8 for stdio; that does not set the default file encoding. No PYTHONUTF8/locale workaround was applied. The product module also has encoding-unspecified writes/read of its approval state; those later paths were NOT executed and are code-review follow-up concerns, not additional runtime failures claimed here.

The real-browser error is only “请求失败（500）”. The failed message stays in the draft; failed attempts are absent from conversation history, and refresh loses the toast. The original before-build instruction with “先不要建模” returned a prose plan in clarify mode, leaving the formal plan button rather than an approval card. The next normal plan-button step exposes the encoding failure. No approval was forged or scope checks disabled.

Native startup separately showed TT_Lib2 missing and InstantRoadPro.rb / SketchUcation 5.0.6 extension errors. Website connection nevertheless reached its own empty model with entity_count=0. No causal link between these third-party extension warnings and the earlier Python approval exception is established. No plugin was installed, updated or removed during this test.

Next repair: make the shared approval/reference state consistently UTF-8, add coverage on a Windows cp936 process using Chinese JSON, and then rerun this same original-reference three-round browser/SU acceptance on a separately frozen fix commit. This is a recommendation; no product fix was made in this acceptance branch.
