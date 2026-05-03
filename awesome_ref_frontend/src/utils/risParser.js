const RIS_TYPES = {
  JOUR: '期刊文章',
  BOOK: '图书',
  CHAP: '书章节',
  CONF: '会议论文',
  THES: '学位论文',
  RPRT: '报告',
  PAT: '专利',
  STD: '标准',
  WEB: '网页',
  GEN: '通用',
};

let idCounter = 0;

export function parseRIS(text) {
  const lines = text.split(/\r?\n/);
  const refs = [];
  let current = null;

  for (const line of lines) {
    const match = line.match(/^([A-Z0-9]{2})\s{2}-\s*(.*)/);
    if (!match) {
      if (current && line.trim()) {
        const lastKey = current._lastKey;
        if (lastKey && ['AB', 'N1', 'N2'].includes(lastKey)) {
          current[lastKey] = (current[lastKey] || '') + ' ' + line.trim();
        }
      }
      continue;
    }

    const tag = match[1];
    const value = match[2].trim();

    if (tag === 'TY') {
      current = {
        id: `ref-${Date.now()}-${idCounter++}`,
        groupId: 'ungrouped',
        type: value,
        title: '',
        authors: [],
        year: '',
        journal: '',
        volume: '',
        issue: '',
        pages: '',
        abstract: '',
        doi: '',
        keywords: [],
        _lastKey: '',
      };
    } else if (tag === 'ER') {
      if (current) {
        const { _lastKey, ...clean } = current;
        refs.push(clean);
        current = null;
      }
    } else if (current) {
      current._lastKey = tag;
      switch (tag) {
        case 'T1': case 'TI': case 'CT':
          if (!current.title) current.title = value;
          break;
        case 'T2': case 'JO': case 'JA': case 'J1': case 'J2':
          if (!current.journal) current.journal = value;
          break;
        case 'AU': case 'A1':
          current.authors.push(value);
          break;
        case 'PY': case 'Y1':
          if (!current.year) current.year = value.split('/')[0];
          break;
        case 'VL':
          if (!current.volume) current.volume = value;
          break;
        case 'IS':
          if (!current.issue) current.issue = value;
          break;
        case 'SP':
          if (!current.pages) {
            current.pages = value;
          } else if (!current.pages.includes('-')) {
            current.pages = value + ' - ' + current.pages;
          }
          break;
        case 'EP':
          if (current.pages && !current.pages.includes('-')) {
            current.pages = current.pages + ' - ' + value;
          } else if (!current.pages) {
            current.pages = value;
          }
          break;
        case 'AB': case 'N2':
          if (!current.abstract) current.abstract = value;
          break;
        case 'DO':
          if (!current.doi) current.doi = value;
          break;
        case 'KW':
          current.keywords.push(value);
          break;
      }
    }
  }

  return refs;
}

export function getRISTypeLabel(type) {
  return RIS_TYPES[type] || type || '未知类型';
}
