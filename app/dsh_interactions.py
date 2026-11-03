"""Per-turn bridge for official DSH questions. No timeout grants permission."""
import copy
import threading
import uuid


class Interactions:
    def __init__(self):
        self._lock = threading.Lock()
        self._rows = {}

    def create(self, data):
        kind = data.get('kind')
        if kind not in ('approval', 'question'):
            raise ValueError('Unknown interaction kind')
        row = {'id': uuid.uuid4().hex, 'kind': kind, 'status': 'pending'}
        if kind == 'approval':
            row.update(tool=str(data.get('tool', ''))[:200], reason=str(data.get('reason', ''))[:8000])
        else:
            questions = data.get('questions')
            if not isinstance(questions, list) or not 1 <= len(questions) <= 20:
                raise ValueError('Questions must be a bounded list')
            ids = []
            for question in questions:
                if not isinstance(question, dict) or not isinstance(question.get('id'), str) or not isinstance(question.get('question'), str):
                    raise ValueError('Invalid question')
                ids.append(question['id'])
            if len(ids) != len(set(ids)):
                raise ValueError('Duplicate question IDs')
            row['questions'] = copy.deepcopy(questions)
        with self._lock:
            self._rows[row['id']] = row
        return self.get(row['id'])

    def get(self, key):
        with self._lock:
            if key not in self._rows:
                raise ValueError('Interaction is no longer available')
            return copy.deepcopy(self._rows[key])

    def pending(self):
        with self._lock:
            return copy.deepcopy([r for r in self._rows.values() if r['status'] == 'pending'])

    def answer(self, key, answer):
        with self._lock:
            row = self._rows.get(key)
            if not row or row['status'] != 'pending':
                raise ValueError('Interaction expired or already answered')
            if row['kind'] == 'approval':
                if answer not in ('allowed-once', 'rejected'):
                    raise ValueError('Explicit allow or reject required')
            else:
                if not isinstance(answer, dict) or not isinstance(answer.get('answers'), list):
                    raise ValueError('Invalid answer')
                by_id = {q['id']: q for q in row['questions']}
                answers = answer['answers']
                if any(not isinstance(a,dict) or not isinstance(a.get('id'),str) for a in answers):
                    raise ValueError('Invalid answer item')
                if len(answers) != len(by_id) or {a.get('id') for a in answers} != set(by_id):
                    raise ValueError('Answer each question exactly once')
                for a in answers:
                    q = by_id[a['id']]
                    selected = a.get('selected', [])
                    labels = {o['label'] for o in q.get('options', [])}
                    if not isinstance(selected, list) or any(not isinstance(s,str) or s not in labels for s in selected):
                        raise ValueError('Unknown selection')
                    if len(selected) != len(set(selected)) or (not q.get('multiSelect') and len(selected) > 1):
                        raise ValueError('Invalid selection count')
                    custom = a.get('custom', '')
                    if not isinstance(custom, str) or len(custom) > 8000 or not (selected or custom.strip()):
                        raise ValueError('Provide a selection or text answer')
            row.update(status='answered', answer=copy.deepcopy(answer))
        return {'ok': True}

    def cancel(self, key=None):
        with self._lock:
            for row in self._rows.values():
                if row['status'] == 'pending' and (key is None or row['id'] == key):
                    row['status'] = 'cancelled'
