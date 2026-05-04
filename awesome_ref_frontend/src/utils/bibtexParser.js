const BIBTEX_TYPE_MAP = {
  article: 'JOUR',
  book: 'BOOK',
  inproceedings: 'CONF',
  conference: 'CONF',
  incollection: 'CHAP',
  inbook: 'CHAP',
  phdthesis: 'THES',
  mastersthesis: 'THES',
  techreport: 'RPRT',
  patent: 'PAT',
  standard: 'STD',
  online: 'WEB',
  webpage: 'WEB',
  misc: 'GEN',
  unpublished: 'GEN',
}

function stripBraces(s) {
  if (!s) return ''
  let t = s.trim()
  while ((t.startsWith('{') && t.endsWith('}')) || (t.startsWith('"') && t.endsWith('"'))) {
    t = t.slice(1, -1).trim()
  }
  t = t.replace(/\{([^}]*)\}/g, '$1')
  return t
}

function parseAuthors(raw) {
  if (!raw) return []
  return raw.split(/\s+and\s+/).map(a => stripBraces(a.trim())).filter(Boolean)
}

function parseKeywords(raw) {
  if (!raw) return []
  return raw.split(/[,;]\s*/).map(k => stripBraces(k.trim())).filter(Boolean)
}

export function parseBibTeX(text) {
  if (!text || !text.trim()) return []

  const entries = text.split(/(?=@\w+\s*\{)/g).filter(e => e.trim())
  const refs = []

  for (const entry of entries) {
    const typeMatch = entry.match(/@(\w+)\s*\{/)
    if (!typeMatch) continue

    const bibType = typeMatch[1].toLowerCase()
    const refType = BIBTEX_TYPE_MAP[bibType] || 'GEN'

    const bodyMatch = entry.match(/@\w+\s*\{[^,]*,\s*([\s\S]*)\s*\}/)
    if (!bodyMatch) continue

    const body = bodyMatch[1]
    const fields = {}

    // Match brace-delimited values: field = {value}
    const bracePattern = /(\w+)\s*=\s*\{([^{}]*)\}/g
    let m
    while ((m = bracePattern.exec(body)) !== null) {
      fields[m[1].toLowerCase()] = m[2]
    }

    // Match quote-delimited values: field = "value" (only for fields not already matched)
    const quotePattern = /(\w+)\s*=\s*"([^"]*)"/g
    while ((m = quotePattern.exec(body)) !== null) {
      if (!(m[1].toLowerCase() in fields)) {
        fields[m[1].toLowerCase()] = m[2]
      }
    }

    const title = stripBraces(fields.title || '')
    let journal = stripBraces(fields.journal || '')
    if (!journal) journal = stripBraces(fields.booktitle || '')

    let pages = ''
    const sp = stripBraces(fields.pages || '')
    if (sp) {
      pages = sp
    } else {
      const start = stripBraces(fields['start-page'] || fields.page || '')
      const end = stripBraces(fields['end-page'] || '')
      if (start && end) pages = start + ' - ' + end
      else if (start) pages = start
    }

    const ref = {
      type: refType,
      title: title || 'Untitled',
      authors: parseAuthors(fields.author),
      year: stripBraces(fields.year || ''),
      journal,
      volume: stripBraces(fields.volume || ''),
      issue: stripBraces(fields.number || fields.issue || ''),
      pages,
      abstract: stripBraces(fields.abstract || fields.annote || ''),
      doi: stripBraces(fields.doi || ''),
      keywords: parseKeywords(fields.keywords || fields.keyword || ''),
    }

    refs.push(ref)
  }

  return refs
}

export function getBibTeXTypeLabel(type) {
  for (const [bibKey, appType] of Object.entries(BIBTEX_TYPE_MAP)) {
    if (appType === type) return bibKey
  }
  return type
}
