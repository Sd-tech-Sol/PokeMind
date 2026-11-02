"""Run a named synthetic suite in a fresh, instrumented process workspace."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from pokemind import synthetic_qa as qa

SUITES = {
    'canary': ['tests/qa_recovery_canary.py'],
    'targeted': ['tests/qa_recovery_targeted.py',
                 'tests/test_synthetic_player_journey.py::test_same_invented_library_public_human_json_html'],
    'core': ['tests/test_synthetic_release_preflight.py', 'tests/test_synthetic_player_journey.py',
             'tests/test_public_source_depth.py', 'tests/test_batch_public_research.py'],
    'qt': ['tests/test_desktop_qt.py', 'tests/test_desktop_workflow_qt.py', 'tests/test_desktop_insights.py', 'tests/test_desktop_i18n.py'],
    'wider': ['tests/test_desktop_services.py', 'tests/test_desktop_ingestion.py',
              'tests/test_public_identity_rules_scoped.py'],
    'launcher': ['tests/qa_offline_gate.py'],
    'cli': ['tests/test_public_evidence_explain_cli.py'],
}
SUITES['all'] = ['tests/qa_recovery_canary.py', 'tests/qa_recovery_targeted.py',
                 *SUITES['core'], *SUITES['qt'], *SUITES['wider'], *SUITES['launcher']]


class Outcomes:
    """Count actual node reports even if JUnit serialization itself fails."""
    def __init__(self):
        self.nodes = {}
        self.collection_errors = 0

    def pytest_runtest_logreport(self, report):
        self.nodes.setdefault(report.nodeid, {})[report.when] = report.outcome

    def pytest_collectreport(self, report):
        self.collection_errors += int(report.failed)

    def counts(self):
        return {'tests': len(self.nodes),
                'tests_called': sum('call' in p for p in self.nodes.values()),
                'passed': sum(p.get('call') == 'passed' and 'failed' not in p.values() for p in self.nodes.values()),
                'failures': sum(p.get('call') == 'failed' for p in self.nodes.values()),
                'errors': self.collection_errors + sum(any(p.get(k) == 'failed' for k in ('setup', 'teardown')) for p in self.nodes.values()),
                'skipped': sum('skipped' in p.values() for p in self.nodes.values())}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--suite', choices=SUITES, required=True)
    args = parser.parse_args()
    context = qa.bootstrap()
    os.environ['QT_QPA_PLATFORM'] = 'windows' if os.name == 'nt' else 'offscreen'
    code, outcomes, junit_counts = 1, Outcomes(), None
    try:
        import pytest
        import platform
        # Pytest JUnit uses platform.node(). Never query the real machine name.
        platform.node = lambda: 'synthetic-qa'
        context.steps.append('pytest_imported')
        junit = context.root / 'junit.xml'
        code = int(pytest.main(['-q', '-x', '--capture=fd', *SUITES[args.suite],
                               '--log-file=' + str(context.log_file),
                               '-o', 'cache_dir=' + str(context.root / 'pytest-cache'),
                               '--basetemp=' + str(context.root / 'pytest-temp'),
                               '--junitxml=' + str(junit)], plugins=[outcomes]))
        if junit.is_file():
            import xml.etree.ElementTree as ET
            suites = list(ET.parse(junit).getroot().iter('testsuite'))
            junit_counts = {k: sum(int(s.get(k, '0')) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
        counts = outcomes.counts()
        if context.denials or not counts['tests_called'] or counts['errors'] or counts['failures']:
            code = 1
    except qa.SecurityIncident:
        code = 2
    except Exception as exc:
        print(json.dumps({'technical_error_category': type(exc).__name__}))
        code = 1
    result = {'task': qa.TASK, 'suite': args.suite, 'exit_code': code,
              **outcomes.counts(), 'junit_counts': junit_counts, **context.summary()}
    if context.denials:
        (context.root / 'guard-local.json').write_text(json.dumps(context.denials, indent=2), encoding='utf-8')
    (context.root / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result))
    return code


if __name__ == '__main__':
    try:
        code = main()
    except Exception as exc:
        print(json.dumps({'startup_error_category': type(exc).__name__, 'details_redacted': True}))
        code = 1
    raise SystemExit(code)
