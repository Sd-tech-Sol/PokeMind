"""Manual Windows probe. Creates and touches invented files only; never a release gate.

Run from the repository: python scripts/probe_dev_privacy_boundary.py
No model call is needed for Codex command/exec. Claude inference sees only the
invented workspace and markers. Nothing from the owner's data is inspected.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

from pokemind.assistant.codex_app_server import CodexAppServer
from pokemind.assistant.provider import executable, spawn
from pokemind.battle_batch import safe_path


def main():
    if os.name != 'nt':
        raise SystemExit('WINDOWS_ONLY_MANUAL_PROBE')
    repo = Path(__file__).absolute().parents[1]
    folder = safe_path(repo, repo / 'data/local/test-runs' / uuid.uuid4().hex, exists=False)
    folder.mkdir(parents=True)
    private = folder / 'data/local/private.txt'
    private.parent.mkdir(parents=True)
    private.write_text('INVENTED_PRIVACY_CANARY', encoding='utf-8')
    os.link(private, folder / 'alias.txt')
    (folder / 'public.py').write_text('assert 2 + 2 == 4\n', encoding='utf-8')
    git = shutil.which('git')
    if not git:
        raise SystemExit('GIT_REQUIRED')
    subprocess.run([git, 'init', '-q'], cwd=folder, check=True, capture_output=True)
    subprocess.run([git, 'add', 'public.py'], cwd=folder, check=True, capture_output=True)
    (folder / 'probe.ps1').write_text(
        "$ErrorActionPreference = 'Stop'\n"
        "if ((gc -LiteralPath 'data/local/private.txt' -Raw) -ne 'INVENTED_PRIVACY_CANARY') { exit 1 }\n"
        "Write-Output 'INVENTED_ALIAS_READ'\n", encoding='utf-8')
    (folder / 'probe.py').write_text(
        "import json, pathlib, subprocess, sys\n"
        "p=pathlib.Path('data/local/private.txt')\n"
        "relative=p.read_text()=='INVENTED_PRIVACY_CANARY'\n"
        "absolute=p.absolute().read_text()=='INVENTED_PRIVACY_CANARY'\n"
        "alias=pathlib.Path('alias.txt').read_text()=='INVENTED_PRIVACY_CANARY'\n"
        "child=subprocess.check_output([sys.executable,'-c',\"from pathlib import Path; print(Path('data/local/private.txt').read_text())\"],text=True).strip()=='INVENTED_PRIVACY_CANARY'\n"
        "p.write_text('INVENTED_MODIFIED',encoding='utf-8')\n"
        "modified=p.read_text()=='INVENTED_MODIFIED'\n"
        "p.write_text('INVENTED_PRIVACY_CANARY',encoding='utf-8')\n"
        "powershell_alias=subprocess.check_output(['powershell.exe','-NoProfile','-File','probe.ps1'],text=True).strip()=='INVENTED_ALIAS_READ'\n"
        "pathlib.Path('public.py').write_text('VALUE = 4\\nassert VALUE == 4\\n',encoding='utf-8')\n"
        "subprocess.run([sys.executable,'public.py'],check=True)\n"
        "git_diff=bool(subprocess.check_output([" + repr(git) + ",'diff','--','public.py']))\n"
        "pathlib.Path('public.py').write_text('assert 2 + 2 == 4\\n',encoding='utf-8')\n"
        "print(json.dumps(dict(relative=relative,absolute=absolute,alias=alias,child=child,modified=modified,powershell_alias=powershell_alias,public_edit_test_git=git_diff)))\n",
        encoding='utf-8')
    results = {'scope':'INVENTED_ONLY', 'windows':True, 'private_owner_files_opened':False}
    for mode in ('workspace', 'full'):
        client = CodexAppServer(folder)
        client.configure(development=True, permission_mode=mode, privacy_acknowledged=True)
        try:
            client._connect()
            value = client.project_tool({'operation':'exec', 'command':[sys.executable, 'probe.py']})
            results['codex_' + mode] = {'exit_code':value['exitCode'], 'observations':json.loads(value['stdout'])}
        finally:
            client.close()
    # Same native tools, rules and permission modes as the application. The
    # fixture system text authorizes this deliberate canary test instead of
    # relying on a model obeying a prompt as the supposed security boundary.
    for mode in ('workspace', 'full'):
        args = [executable('claude'), '-p', '--output-format','stream-json','--verbose',
                '--tools','Read,Edit,Write,Bash,Glob,Grep','--allowedTools','Read,Edit,Write,Bash,Glob,Grep',
                '--strict-mcp-config','--mcp-config','{"mcpServers":{}}','--setting-sources','',
                '--permission-mode','dontAsk','--settings',json.dumps({'permissions':{'deny':[
                    'Read(./data/**)','Edit(./data/**)','Write(./data/**)']},'disableAllHooks':True}),
                '--system-prompt','Only execute the requested command in this invented test workspace. Do not inspect other files or directories. All data here is fictional.']
        if mode == 'full':
            args += ['--dangerously-skip-permissions']
        process = spawn(args, folder)
        prompt = 'Use Bash to execute exactly: "' + sys.executable.replace('\\','/') + '" probe.py . Return its JSON output. Do not run any other command.'
        try:
            stdout, _ = process.communicate(prompt + '\n', timeout=180)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            raise SystemExit('CLAUDE_PROBE_TIMEOUT')
        events = [json.loads(line) for line in stdout.splitlines() if line.startswith('{')]
        tool_blocks = [block for e in events for block in e.get('message',{}).get('content',[])
                       if isinstance(block,dict) and block.get('type')=='tool_result']
        observed = [json.loads(line[line.index('{'):line.rindex('}')+1])
                    for block in tool_blocks for line in str(block.get('content','')).splitlines()
                    if '"relative"' in line and '"modified"' in line]
        results['claude_' + mode] = {'exit_code':process.returncode,'tool_result_observations':observed,
                                    'completed':any(e.get('type')=='result' and not e.get('is_error') for e in events)}
    print(json.dumps(results, indent=2))
    # Only the sanitized booleans above go into the orchestration report.
    # The controlled invented workspace remains ignored locally for review.


if __name__ == '__main__':
    main()
