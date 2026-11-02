"""Explicit startup canary with real pytest FD capture and file logger."""
import json
import logging
import os
import tempfile
import platform
from pathlib import Path

import pytest
from pokemind import synthetic_qa as qa


def test_temp_capture_log_fixture_and_junit(local_tmp, request):
    context = qa.current()
    assert context.validate_live() == context.root.resolve(strict=True)
    assert Path(tempfile.gettempdir()) == context.temp
    assert all(os.environ[k] == str(context.temp) for k in ('TEMP', 'TMP', 'TMPDIR'))
    assert local_tmp.parent == context.root and len(local_tmp.name) == 32
    assert request.config.getoption('capture') == 'fd'
    assert Path(request.config.getoption('xmlpath')) == context.root / 'junit.xml'
    assert Path(request.config.getoption('log_file')) == context.log_file
    assert context.log_file.is_file()
    assert platform.node() == 'synthetic-qa'
    assert context.before_conftest >= 2
    assert context.steps.index('tempfile_configured_before_pytest') < context.steps.index('pytest_imported')
    with tempfile.NamedTemporaryFile(delete=False) as stream:
        stream.write(b'entirely invented QA canary')
        assert Path(stream.name).parent == context.temp
    assert context.tempfiles and all(p.startswith(context.temp.name + '/') for p in context.tempfiles)
    # Inspect the exact old logger normalization, without opening that target.
    handler = logging.FileHandler(os.devnull, delay=True)
    try:
        assert handler.stream is None
        diagnostic = {'input': os.devnull, 'normalized_target': handler.baseFilename,
                      'opened': False, 'pytest_log_is_explicit_in_workspace': True}
        (context.root / 'logger-target-local.json').write_text(json.dumps(diagnostic), encoding='utf-8')
    finally:
        handler.close()
    with pytest.raises(PermissionError, match='QA_PRIVATE_NAMESPACE_REFUSED'):
        context.policy.path(qa.PROJECT / 'data/local/DO_NOT_OPEN', write=True)
    source, alias = local_tmp / 'invented', local_tmp / 'alias'
    source.write_text('invented', encoding='utf-8'); os.link(source, alias)
    with pytest.raises(ValueError, match='QA_FILE_ALIAS_REFUSED'):
        qa.no_alias(alias, context.root)
    assert not context.denials and not context.security_incident
