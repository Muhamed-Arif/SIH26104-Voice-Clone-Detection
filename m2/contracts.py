"""Member 3 handoff helpers. These create payloads; they do not send audio."""
from datetime import datetime
import uuid
from .stream_microphone import prepare, quality


def backend_chunk(samples, source_rate, chunk_id, timestamp, session_id=None):
    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    if not chunk_id.strip():
        raise ValueError('chunk_id is required')
    x = prepare(samples, source_rate)
    if not 8000 <= len(x) <= 32000:
        raise ValueError('Backend handoff requires 0.5..2 second windows')
    q = quality(x)['quality']
    if q == 'SILENCE':
        raise ValueError('Skip silence before backend submission')
    result = {'waveform': x.tolist(), 'sample_rate': 16000, 'chunk_id': chunk_id,
              'quality': q, 'timestamp': timestamp}
    if session_id:
        result['session_id'] = str(uuid.UUID(session_id))
    return result


def m1_payload(chunk, language):
    """Translate DSPAudioChunk to the strict M1 JSON contract."""
    if language not in ('English', 'Hindi', 'Tamil'):
        raise ValueError('Unsupported language')
    if not isinstance(chunk['waveform'], list):
        raise ValueError('Decode base64 audio to mono floats before calling M1')
    return {'waveform': chunk['waveform'], 'sample_rate': chunk['sample_rate'],
            'chunk_id': chunk['chunk_id'], 'language': language}
