"""Bounded derived-field extraction for the existing PUBLIC snapshots.

Experimental grammar, exercised on authored fixtures only. No network, page
retention, normative promotion, or implicit real-source licence approval.
"""
from __future__ import annotations

import re
from datetime import date
from html.parser import HTMLParser

EXTRACTOR = 'public-rotation-fields-v1'


def iso_day(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def retention_allowed(policy):
    # No real-site licence is established by this technical mandate. Only the
    # authored synthetic fixture licence is admitted; production stays closed.
    return (isinstance(policy, dict) and policy.get('mode') == 'derived_fields_only'
            and policy.get('license') == 'synthetic_author_owned'
            and isinstance(policy.get('reference'), str)
            and bool(re.fullmatch(r'[a-zA-Z0-9_-]{1,80}', policy['reference'])))


class _Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.article = 0
        self.excluded = []
        self.current = None
        self.paragraphs = []
        self.publications = []
        self.overflow = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.excluded or tag in {'script','style','template','nav','aside','footer'} or 'hidden' in attrs:
            self.excluded.append(tag)
            return
        if tag == 'meta' and attrs.get('property') == 'article:published_time':
            self.publications.append(attrs.get('content'))
        if tag == 'article':
            self.article += 1
        if tag == 'p' and self.article:
            self.current = []

    def handle_endtag(self, tag):
        if self.excluded:
            if tag in self.excluded:
                self.excluded = self.excluded[:self.excluded.index(tag)]
            return
        if tag == 'p' and self.current is not None:
            text = ' '.join(''.join(self.current).split())
            if len(self.paragraphs) < 64 and len(text) <= 500:
                self.paragraphs.append(text)
            else:
                self.overflow = True
            self.current = None
        if tag == 'article':
            self.article = max(0,self.article-1)

    def handle_data(self, data):
        if not self.excluded and self.current is not None:
            if sum(map(len,self.current)) + len(data) <= 1000:
                self.current.append(data)
            else:
                self.overflow = True


def extract_official_fields(body, *, source_url, policy):
    """Keep only typed facts, never titles, snippets, or complete HTML bodies.

    Refusing unsupported prose is deliberate; this is no general NLP parser.
    A later real collection needs separate rights and grammar validation.
    """
    from pokemind.batch_public_research import allowed_url
    if allowed_url(source_url) != 'www.pokemon.com' or source_url.endswith('/robots.txt'):
        raise ValueError('OFFICIAL_SOURCE_NOT_ADMITTED')
    result = {'extractor':EXTRACTOR, 'status':'RETENTION_NOT_AUTHORIZED',
              'published_at':None, 'assertions':[], 'raw_retained':False}
    if not retention_allowed(policy):
        return result
    result['rights'] = {k:policy[k] for k in ('mode','license','reference')}
    if len(body) > 2*1024*1024:
        return result | {'status':'EXTRACTION_SIZE_CAP'}
    parser = _Paragraphs()
    parser.feed(body.decode('utf-8', errors='replace'))
    published = {iso_day(p) for p in parser.publications}
    result['published_at'] = next(iter(published)) if len(published)==1 else None
    rows = []
    for paragraph in parser.paragraphs:
        match = re.fullmatch(r'In the Standard format for (TCG Live|in-person play), '
            r'regulation marks ([A-Z](?:, [A-Z]){0,7}) are allowed(?: starting (\d{4}-\d{2}-\d{2}))?\.', paragraph)
        if not match:
            continue
        platform, marks, effective = match.groups()
        row = {'assertion_kind':'rotation', 'format':'standard',
               'platform':'live' if platform=='TCG Live' else 'in_person',
               'allowed_regulation_marks':sorted(set(marks.split(', '))),
               'effective_from':iso_day(effective),
               'date_issue':('EFFECTIVE_DATE_MISSING_OR_INVALID' if effective else 'EFFECTIVE_DATE_MISSING')
                            if not iso_day(effective) else None}
        if row not in rows:
            rows.append(row)
    if parser.overflow or len(rows)>8:
        return result | {'status':'EXTRACTION_SIZE_CAP'}
    return result | {'status':'extracted_unverified' if rows else 'TEXT_ABSENT_OR_UNSUPPORTED',
                     'assertions':rows}


def qualified_rule_fields(fact, *, as_of=None, conflicts=(), text=str, join=str.join):
    """Re-qualify at consultation time; source observations never become law."""
    from pokemind.batch_public_research import allowed_url
    try:
        if allowed_url(fact['source_url'])!='www.pokemon.com' or fact['source_url'].endswith('/robots.txt'):
            return []
    except (KeyError,ValueError,TypeError):
        return []
    evidence = fact.get('rule_evidence')
    if not isinstance(evidence,dict) or evidence.get('extractor')!=EXTRACTOR:
        return []
    if not retention_allowed(evidence.get('rights')):
        return [text('Extraction : ') + 'RETENTION_NOT_AUTHORIZED' + text('; application courante : unknown.')]
    status = evidence.get('status')
    if status != 'extracted_unverified':
        status = status if status in {'TEXT_ABSENT_OR_UNSUPPORTED','EXTRACTION_SIZE_CAP'} else 'unknown'
        return [text('Extraction : ') + status + text('; application courante : unknown.')]
    rows = evidence.get('assertions')
    if not isinstance(rows,list) or len(rows)>8:
        return [text('Extraction : unknown; application courante : unknown.')]
    published, cutoff = iso_day(evidence.get('published_at')), iso_day(as_of)
    output = []
    for row in rows:
        if not isinstance(row,dict) or row.get('assertion_kind')!='rotation' or row.get('format')!='standard':
            continue
        platform, marks = row.get('platform'),row.get('allowed_regulation_marks')
        if platform not in {'live','in_person'} or not isinstance(marks,list) or not 1<=len(marks)<=8 or any(
                not isinstance(m,str) or not re.fullmatch('[A-Z]',m) for m in marks):
            continue
        effective = iso_day(row.get('effective_from'))
        issue = ('CONFLICTING_ASSERTIONS' if platform in conflicts else
                 'PUBLICATION_DATE_MISSING_OR_INVALID' if not published else
                 'AS_OF_MISSING' if not cutoff else 'FUTURE_PUBLICATION' if published>cutoff else
                 ('EFFECTIVE_DATE_MISSING_OR_INVALID' if row.get('date_issue')=='EFFECTIVE_DATE_MISSING_OR_INVALID'
                  else 'EFFECTIVE_DATE_MISSING') if not effective else
                 'NOT_YET_EFFECTIVE' if effective>cutoff else 'UNVERIFIED_NORMATIVE_SOURCE')
        label = 'TCG Live' if platform=='live' else text('en personne')
        output += [join('', [text('Champs extraits (extracted_unverified) : rotation Standard, plateforme '), label,
                   text('; marques rapportées : '), ', '.join(marks), text('; publication : '), published or 'unknown',
                   text('; date d’effet annoncée : '), effective or 'unknown', '.']),
                   text('Qualification : ') + issue + text('; application courante : unknown.')]
    output.append(text('Équivalence de réimpression : unknown; disponibilité dans Live : unknown; restrictions et texte effectif non certifiés.'))
    return output


def conflicting_platforms(facts):
    """Conservative across admitted current snapshots, including revisions."""
    from pokemind.batch_public_research import allowed_url
    claims = {}
    for fact in facts:
        try:
            if fact.get('kind')!='official_document' or allowed_url(fact['source_url'])!='www.pokemon.com':
                continue
        except (KeyError,ValueError,TypeError):
            continue
        evidence = fact.get('rule_evidence') or {}
        if (not isinstance(evidence,dict) or evidence.get('extractor')!=EXTRACTOR
                or not retention_allowed(evidence.get('rights'))):
            continue
        rows = evidence.get('assertions')
        if not isinstance(rows,list):
            continue
        for row in rows[:8]:
            if isinstance(row,dict):
                marks = row.get('allowed_regulation_marks')
                if (isinstance(marks,list) and all(isinstance(m,str) for m in marks)
                        and isinstance(row.get('effective_from'),(str,type(None)))):
                    claims.setdefault(row.get('platform'),set()).add((tuple(sorted(marks)),row.get('effective_from')))
    return {platform for platform,rows in claims.items() if len(rows)>1}
