"""Evaluate labeled WAV files against the running M1 model; no microphone required.
CSV columns: path,label,language. label is REAL or AI_GENERATED.
Run: python -m m2.evaluate --manifest m2/my_samples.csv --output m2/logs/evaluation.json
"""
import argparse
import csv
import io
import json
from pathlib import Path

from .stream_microphone import Runner, parser as stream_parser, run_file


def summarize(rows):
    matrix = {'true_real': 0, 'false_positive': 0, 'false_negative': 0, 'true_ai': 0}
    eligible = 0
    for row in rows:
        if row['predicted'] not in ('REAL', 'AI_GENERATED'):
            continue
        eligible += 1
        expected, predicted = row['label'], row['predicted']
        key = ('true_real' if predicted == 'REAL' else 'false_positive') if expected == 'REAL' else (
            'false_negative' if predicted == 'REAL' else 'true_ai')
        matrix[key] += 1
    return {'files': len(rows), 'classified_files': eligible,
            'inconclusive_or_failed_files': len(rows)-eligible, 'confusion_matrix': matrix,
            'accuracy_on_classified_files': (matrix['true_real']+matrix['true_ai'])/eligible if eligible else None,
            'decision_rule': 'Majority of valid M1 chunk labels; ties, API failures and no usable chunks are inconclusive.',
            'note': 'Overlapping chunks are correlated. This report scores files, not independent windows.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--api-url', default='http://127.0.0.1:8001')
    args = p.parse_args()
    with args.manifest.open(newline='', encoding='utf-8-sig') as f:
        inputs = list(csv.DictReader(f))
    if not inputs:
        p.error('Manifest contains no samples')
    rows = []
    for item in inputs:
        if item.get('label') not in ('REAL', 'AI_GENERATED') or item.get('language') not in ('English', 'Hindi', 'Tamil'):
            p.error('Every row needs label REAL/AI_GENERATED and language English/Hindi/Tamil')
        source = Path(item['path'])
        if not source.is_absolute():
            source = args.manifest.parent/source
        options = stream_parser().parse_args(['--file', str(source), '--api-url', args.api_url, '--language', item['language']])
        log = io.StringIO()
        runner = Runner(options, log)
        error = None
        try:
            runner.api.health()
            run_file(runner)
        except Exception as exc:
            error = str(exc)
            runner.failed = True
        chunks = [json.loads(line) for line in log.getvalue().splitlines()]
        labels = [r['status'] for r in chunks if r.get('status') in ('REAL', 'AI_GENERATED')]
        real, ai = labels.count('REAL'), labels.count('AI_GENERATED')
        predicted = 'INCONCLUSIVE' if runner.failed or real == ai else ('REAL' if real > ai else 'AI_GENERATED')
        rows.append({'path': item['path'], 'label': item['label'], 'language': item['language'],
                     'predicted': predicted, 'error': error, 'chunks': chunks})
    result = {'summary': summarize(rows), 'results': rows}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False), encoding='utf-8')
    print(json.dumps(result['summary'], indent=2))
    print(f'Report: {args.output.resolve()}')


if __name__ == '__main__':
    main()
