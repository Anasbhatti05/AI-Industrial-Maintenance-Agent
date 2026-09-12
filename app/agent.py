from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Iterable, List

import pandas as pd
from openai import OpenAI
from pypdf import PdfReader

from app.config import MODEL_NAME, OPENAI_API_KEY, GROQ_API_KEY

try:
    from core.agent import diagnose_incident as core_diagnose_incident
except Exception:
    core_diagnose_incident = None

DATA_PATH = Path(__file__).resolve().parent.parent / 'data' / 'AI_Industrial_Maintenance_Knowledge_Base_Final-1.xlsx'


def _detect_language(text: str) -> str:
    return 'en'


def _normalise(text: str, language: str | None = None) -> str:
    if not text:
        return ''
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text


def _weight_match_score(issue_text: str, row: pd.Series, equipment_text: str = '') -> float:
    issue_tokens = set(_normalise(issue_text).split())
    if not issue_tokens:
        return 0.0

    score = 0.0
    row_parts = {
        'fault': str(row.get('Fault / Incident', '')),
        'symptoms': str(row.get('Symptoms', '')),
        'causes': str(row.get('Possible Causes', '')),
        'tags': str(row.get('Keywords / Tags', '')),
        'guidance': str(row.get('Troubleshooting Guidance', '')),
    }

    for label, text in row_parts.items():
        tokens = set(_normalise(text).split())
        if not tokens:
            continue
        matches = len(issue_tokens & tokens)
        if matches == 0:
            continue
        weights = {'fault': 7.0, 'symptoms': 3.5, 'causes': 2.8, 'tags': 2.0, 'guidance': 1.5}
        score += matches * weights.get(label, 1.0)

    issue_lower = (issue_text or '').lower()
    row_fault = _normalise(str(row.get('Fault / Incident', '')))
    row_machine = _normalise(str(row.get('Machine', '')))
    row_text = ' '.join(row_parts.values()).lower()
    equipment_tokens = set(_normalise(equipment_text).split()) if equipment_text else set()

    if equipment_tokens:
        if equipment_tokens & set(row_machine.split()):
            score += 28.0
        if any(token in {'water', 'pani', 'pump'} for token in equipment_tokens) and 'water pump' in row_machine:
            score += 35.0
        if 'motor' in equipment_tokens and 'motor' in row_machine:
            score += 18.0

    explicit_boosts = {
        'overheat': ['overheating', 'temperature', 'hot', 'heat'],
        'vibration': ['vibration', 'vibrating', 'vibrating', 'shake', 'misalignment', 'alignment'],
        'noise': ['noise', 'grinding', 'humming', 'sound', 'squeal'],
        'start': ['start', 'startup', 'trip', 'no start'],
        'slip': ['slip', 'slipping', 'drive'],
        'flow': ['flow', 'pressure', 'low flow'],
        'blockage': ['blockage', 'clog', 'overload'],
        'belt': ['belt', 'mistrack', 'tracking'],
    }

    for key, values in explicit_boosts.items():
        if key in issue_lower and any(value in row_fault or value in row_text for value in values):
            score += 18.0

    if 'vibrat' in issue_lower and 'excessive vibration' in row_fault:
        score += 25.0
    if 'overheat' in issue_lower and 'overheating' in row_fault:
        score += 25.0
    if 'noise' in issue_lower and 'abnormal noise' in row_fault:
        score += 20.0
    if 'slip' in issue_lower and 'belt slippage' in row_fault:
        score += 22.0
    if 'flow' in issue_lower and 'reduced flow' in row_fault:
        score += 22.0
    if 'pani' in issue_tokens and 'water pump' in row_machine:
        score += 30.0
    if 'water' in issue_tokens and 'water pump' in row_machine:
        score += 30.0
    if 'aag' in issue_tokens and 'water pump' in row_machine and 'overheating' in row_fault:
        score += 25.0

    return score


def _load_knowledge() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return pd.DataFrame(columns=['Machine', 'Fault / Incident', 'Severity', 'Symptoms', 'Possible Causes', 'Troubleshooting Guidance'])

    xls = pd.ExcelFile(DATA_PATH)
    if 'Knowledge Base' in xls.sheet_names:
        df = xls.parse('Knowledge Base')
    else:
        df = xls.parse(0)

    expected_cols = ['Machine', 'Fault / Incident', 'Severity', 'Symptoms', 'Possible Causes', 'Troubleshooting Guidance']
    for col in expected_cols:
        if col not in df.columns:
            df[col] = ''

    return df


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> List[str]:
    if not text:
        return []
    cleaned = re.sub(r'\s+', ' ', text).strip()
    chunks = []
    start = 0
    while start < len(cleaned):
        end = min(start + chunk_size, len(cleaned))
        chunk = cleaned[start:end]
        chunks.append(chunk)
        if end == len(cleaned):
            break
        start = max(start + chunk_size - overlap, end - overlap)
    return chunks


def _extract_pdf_text(file_obj) -> str:
    try:
        read_bytes = file_obj.read()
    except Exception:
        read_bytes = file_obj.getvalue() if hasattr(file_obj, 'getvalue') else b''

    if not read_bytes:
        return ''

    if isinstance(file_obj, (str, Path)):
        with open(file_obj, 'rb') as fh:
            reader = PdfReader(fh)
            pages = [page.extract_text() or '' for page in reader.pages]
            return '\n'.join(pages)

    try:
        reader = PdfReader(file_obj)
    except Exception:
        import io
        reader = PdfReader(io.BytesIO(read_bytes))

    texts = [page.extract_text() or '' for page in reader.pages]
    return '\n'.join(texts)


def _pdf_matches(issue_text: str, files: Iterable) -> List[dict]:
    if not files:
        return []

    issue_tokens = set(_normalise(issue_text).split())
    matches = []

    for file_obj in files:
        try:
            text = _extract_pdf_text(file_obj)
        except Exception:
            continue

        chunks = _chunk_text(text)
        for idx, chunk in enumerate(chunks):
            score = sum(1 for token in issue_tokens if token and token in _normalise(chunk).split())
            if score > 0:
                matches.append({
                    'source': getattr(file_obj, 'name', f'pdf_{idx + 1}'),
                    'chunk': chunk[:500],
                    'score': score,
                })

    matches = sorted(matches, key=lambda item: item['score'], reverse=True)
    return matches[:3]


def _summarize_with_llm(summary_text: str, issue_text: str, equipment: str, possible_causes: list[str] | None = None, recommended_actions: list[str] | None = None) -> str:
    if GROQ_API_KEY and core_diagnose_incident is not None:
        try:
            agent_response = core_diagnose_incident(
                machine=equipment or 'Unknown Equipment',
                problem=issue_text,
                additional_information=summary_text,
            )
            if agent_response and agent_response.strip():
                return agent_response.strip()
        except Exception:
            pass

    api_key = OPENAI_API_KEY or GROQ_API_KEY
    if not api_key:
        return summary_text

    try:
        client_kwargs = {'api_key': api_key}
        if GROQ_API_KEY and not OPENAI_API_KEY:
            client_kwargs['base_url'] = 'https://api.groq.com/openai/v1'
        client = OpenAI(**client_kwargs)

        system_prompt = 'You are an industrial maintenance expert. Write concise, practical, safety-aware advice.'
        user_prompt = (
            f'Equipment: {equipment}\n'
            f'Issue: {issue_text}\n'
            f'Context: {summary_text}\n\n'
            'Provide a short diagnosis summary, likely root causes, and recommended next steps.'
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt
                },
                {
                    'role': 'user',
                    'content': user_prompt
                }
            ],
            temperature=0.2,
            max_tokens=300,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return summary_text


def _derive_severity_and_priority(issue_text: str, matches: list[dict]) -> tuple[str, int]:
    severity_rank = {'Low': 1, 'Medium': 2, 'High': 3, 'Critical': 4}
    issue_lower = (issue_text or '').lower()
    severities = [str(match.get('Severity', 'Medium')).strip().title() for match in matches]
    severity = 'Medium'
    if severities:
        severity = max(severities, key=lambda item: severity_rank.get(item, 2))

    if 'fire' in issue_lower or 'smoke' in issue_lower or 'sudden shutdown' in issue_lower:
        severity = 'Critical'
    elif 'overheat' in issue_lower or 'vibration' in issue_lower or 'noise' in issue_lower:
        if severity in {'Low', 'Medium'}:
            severity = 'High'

    score = {'Low': 35, 'Medium': 55, 'High': 75, 'Critical': 90}[severity]
    if 'overheat' in issue_lower:
        score = min(score + 8, 100)
    if 'safety' in issue_lower:
        score = min(score + 5, 100)
    return severity, score


def analyze_issue(issue_text: str, equipment: str = '', files: Iterable | None = None) -> dict:
    """Use Excel records and optionally uploaded PDF manuals to identify likely faults."""
    raw_issue = issue_text or ''
    language = _detect_language(raw_issue)
    issue_norm = _normalise(raw_issue, language)
    equipment_norm = _normalise(equipment, language)
    df = _load_knowledge()

    pdf_matches = _pdf_matches(raw_issue, files or [])

    if df.empty and not pdf_matches:
        fallback = {
            'equipment': equipment,
            'issue_summary': raw_issue,
            'possible_causes': ['No maintenance knowledge found. Review machine logs and manuals.'],
            'recommended_actions': [
                'Inspect the current machine state',
                'Check recent maintenance logs',
                'Escalate to a technician if the issue is critical'
            ],
            'matches': [],
            'knowledge_summary': 'No data available.',
            'llm_summary': '',
            'severity': 'Medium',
            'priority_score': 55,
        }
        return fallback

    if not df.empty:
        df['search_text'] = (
            df['Machine'].fillna('') + ' ' +
            df['Fault / Incident'].fillna('') + ' ' +
            df['Symptoms'].fillna('') + ' ' +
            df['Possible Causes'].fillna('') + ' ' +
            df['Troubleshooting Guidance'].fillna('')
        ).map(_normalise)

        filtered = df.copy()
        if equipment_norm:
            filtered = filtered[filtered['Machine'].fillna('').map(_normalise).str.contains(equipment_norm, na=False)]

        if filtered.empty:
            filtered = df

        issue_tokens = set(issue_norm.split())
        filtered = filtered.assign(score=filtered.apply(lambda row: _weight_match_score(raw_issue, row), axis=1)).copy()
        filtered = filtered.sort_values(['score', 'Machine'], ascending=[False, True], kind='mergesort')
        matches = filtered.head(3).copy()

        if matches.empty or matches['score'].max() == 0:
            matches = df.head(3).copy()
            matches['score'] = 1

        likely_causes = []
        recommended_actions = []
        summary_rows = []

        for _, row in matches.iterrows():
            if row.get('Possible Causes'):
                likely_causes.extend([item.strip() for item in str(row['Possible Causes']).split(';') if item.strip()])
            if row.get('Troubleshooting Guidance'):
                recommended_actions.append(str(row['Troubleshooting Guidance']).strip())
            summary_rows.append({
                'Machine': row.get('Machine', ''),
                'Fault / Incident': row.get('Fault / Incident', ''),
                'Severity': row.get('Severity', ''),
                'Possible Causes': row.get('Possible Causes', ''),
                'Troubleshooting Guidance': row.get('Troubleshooting Guidance', '')
            })
    else:
        likely_causes = []
        recommended_actions = []
        summary_rows = []

    if pdf_matches:
        pdf_cause_lines = []
        for match in pdf_matches:
            chunk = match['chunk']
            if ':' in chunk:
                pdf_cause_lines.append(chunk)
            else:
                pdf_cause_lines.append('Review relevant section for: ' + chunk[:120])
        if pdf_cause_lines:
            likely_causes.extend(pdf_cause_lines[:2])
        if not recommended_actions:
            recommended_actions = ['Review the uploaded manual section and verify the relevant operating conditions.']

    if not likely_causes:
        likely_causes = ['Review the machine manual and check recent operating conditions.']
    if not recommended_actions:
        recommended_actions = [
            'Inspect the machine for wear, vibration, and overheating.',
            'Check alarms, maintenance logs, and recent operating conditions.',
            'Escalate to a qualified technician if the issue is severe.'
        ]

    summary_text = (
        f'Equipment: {equipment or "Unknown"}\n'
        f'Issue: {raw_issue}\n'
        f'Likely causes: {"; ".join(likely_causes[:4])}\n'
        f'Recommended actions: {"; ".join(recommended_actions[:4])}'
    )
    llm_summary = _summarize_with_llm(summary_text, raw_issue, equipment or 'Unknown equipment', likely_causes[:4], recommended_actions[:4])

    result_matches = summary_rows + [
        {
            'Machine': item['source'],
            'Fault / Incident': 'Uploaded PDF match',
            'Severity': 'N/A',
            'Possible Causes': item['chunk'][:200],
            'Troubleshooting Guidance': 'Review the uploaded manual section for context.'
        }
        for item in pdf_matches
    ]
    severity, priority_score = _derive_severity_and_priority(raw_issue, result_matches)

    knowledge_summary = 'Knowledge base and uploaded manual content were used to identify relevant guidance.' if pdf_matches else 'Knowledge base matched relevant maintenance records and troubleshooting guidance.'

    return {
        'equipment': equipment or (matches.iloc[0].get('Machine', '') if 'matches' in locals() and not matches.empty else ''),
        'issue_summary': raw_issue,
        'possible_causes': likely_causes[:4],
        'recommended_actions': recommended_actions[:4],
        'matches': result_matches,
        'knowledge_summary': knowledge_summary,
        'llm_summary': llm_summary,
        'severity': severity,
        'priority_score': priority_score,
        'language': language,
    }
