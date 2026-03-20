// Client-side IP allocator for GitHub Pages (browser-only).
// Basic IPv4 helper functions and allocation logic, then UI wiring.

// Convert dotted IPv4 string to unsigned 32-bit integer.
function ipToInt(ip) {
  const parts = ip.trim().split('.');
  if (parts.length !== 4) throw new Error('Invalid IPv4 address: ' + ip);
  return parts.reduce((acc, p) => {
    const n = Number(p);
    if (!Number.isInteger(n) || n < 0 || n > 255) throw new Error('Invalid IPv4 octet: ' + p);
    return (acc << 8) + n;
  }, 0) >>> 0;
}

// Convert unsigned 32-bit integer to dotted IPv4 string.
function intToIp(i) {
  i = i >>> 0;
  return [(i >>> 24) & 0xff, (i >>> 16) & 0xff, (i >>> 8) & 0xff, i & 0xff].join('.');
}

// Parse a CIDR like "10.0.0.0/24" -> {network: int, prefix: number, first:int, last:int}
function parseCidr(cidr) {
  if (typeof cidr !== 'string') throw new Error('CIDR must be a string');
  const parts = cidr.trim().split('/');
  if (parts.length !== 2) throw new Error('Invalid CIDR: ' + cidr);
  const ip = parts[0].trim();
  const prefix = Number(parts[1]);
  if (!Number.isInteger(prefix) || prefix < 0 || prefix > 32) throw new Error('Invalid prefix in CIDR: ' + cidr);
  const ipInt = ipToInt(ip);
  const mask = prefix === 0 ? 0 : (0xFFFFFFFF << (32 - prefix)) >>> 0;
  const network = ipInt & mask;
  const broadcast = network | (~mask >>> 0);
  return { network, prefix, first: network, last: broadcast };
}

// Normalize existing input (string with newlines or array)
function normalizeExisting(existingField) {
  if (!existingField) return [];
  if (typeof existingField === 'string') {
    return existingField.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
  }
  if (Array.isArray(existingField)) {
    return existingField.flatMap(item => {
      if (typeof item !== 'string') item = String(item);
      return item.split(/\r?\n/).map(s => s.trim()).filter(Boolean);
    });
  }
  return [String(existingField).trim()].filter(Boolean);
}

// Check if two ranges [a1,a2] and [b1,b2] overlap
function rangesOverlap(a1, a2, b1, b2) {
  return !(a2 < b1 || b2 < a1);
}

// Generate all candidate subnets (as objects) inside overall and include overlaps with existing.
// Each candidate: {subnet: '10.0.0.0/26', overlaps: ['10.0.0.0/27', ...] }
function candidatesWithCollisions(overallCidr, existingList, targetPrefix) {
  const overall = parseCidr(overallCidr);
  const existing = existingList.map(parseCidr);
  if (targetPrefix < overall.prefix) throw new Error(`target prefix /${targetPrefix} must be >= overall /${overall.prefix}`);
  if (targetPrefix > 32 || targetPrefix < 0) throw new Error('prefix length must be between 0 and 32');

  const subSize = Math.pow(2, 32 - targetPrefix);
  const num = Math.pow(2, targetPrefix - overall.prefix);
  const result = [];
  for (let i = 0; i < num; i++) {
    const base = (overall.network + i * subSize) >>> 0;
    const first = base;
    const last = (base + subSize - 1) >>> 0;
    const overlaps = [];
    for (const ex of existing) {
      if (rangesOverlap(first, last, ex.first, ex.last)) {
        overlaps.push(`${intToIp(ex.network)}/${ex.prefix}`);
      }
    }
    result.push({ subnet: `${intToIp(base)}/${targetPrefix}`, overlaps });
  }
  return result;
}

// Generate only non-conflicting candidate subnets (returns objects like above with empty overlaps)
function generateAvailableCandidates(overallCidr, existingList, targetPrefix) {
  const all = candidatesWithCollisions(overallCidr, existingList, targetPrefix);
  return all.filter(c => !c.overlaps || c.overlaps.length === 0);
}

// UI wiring
document.addEventListener('DOMContentLoaded', () => {
  const overallEl = document.getElementById('overall');
  const existingEl = document.getElementById('existing');
  const prefixEl = document.getElementById('prefix');
  const checkBtn = document.getElementById('ajax-check');
  const spinner = document.getElementById('spinner');
  const resultsContent = document.getElementById('results-content');
  const availableList = document.getElementById('available-list');
  const availableCount = document.getElementById('available-count');
  const summary = document.getElementById('summary');
  const formError = document.getElementById('form-error');
  const copyAllBtn = document.getElementById('copy-all');
  const debugToggle = document.getElementById('filter-toggle');
  const debugSection = document.getElementById('debug-section');
  const debugList = document.getElementById('debug-list');
  const downloadJsonBtn = document.getElementById('download-json');
  const jsonPre = document.getElementById('json-pre');
  const jsonSection = document.getElementById('json-section');

  function showSpinner(on) { spinner.style.display = on ? 'block' : 'none'; }
  function showError(msg) { formError.style.display = 'block'; formError.textContent = msg; }
  function clearError() { formError.style.display = 'none'; formError.textContent = ''; }

  async function doCheck() {
    clearError();
    resultsContent.style.display = 'none';
    showSpinner(true);
    try {
      const overall = overallEl.value.trim();
      const existingRaw = existingEl.value;
      const prefix = Number(prefixEl.value);

      if (!overall) throw new Error('Overall CIDR is required');
      if (!Number.isInteger(prefix) || prefix < 0 || prefix > 32) throw new Error('Prefix must be integer between 0 and 32');

      const existing = normalizeExisting(existingRaw);

      // Validate existing entries; parseCidr will throw on invalid entries
      for (const e of existing) parseCidr(e);

      const candidatesAll = candidatesWithCollisions(overall, existing, prefix);
      const available = candidatesAll.filter(c => !c.overlaps || c.overlaps.length === 0);

      // Render available
      availableList.innerHTML = '';
      if (available.length === 0) {
        const li = document.createElement('li');
        li.className = 'none';
        li.textContent = '(none)';
        availableList.appendChild(li);
      } else {
        for (const c of available) {
          const li = document.createElement('li');
          li.className = 'available-item';
          const code = document.createElement('code');
          code.textContent = c.subnet;
          const btn = document.createElement('button');
          btn.className = 'btn tiny';
          btn.textContent = 'Copy';
          btn.type = 'button';
          btn.addEventListener('click', async () => {
            await navigator.clipboard.writeText(c.subnet);
            btn.textContent = 'Copied';
            setTimeout(() => btn.textContent = 'Copy', 1000);
          });
          li.appendChild(code);
          li.appendChild(btn);
          availableList.appendChild(li);
        }
      }

      // Debug list (all candidates and collisions)
      debugList.innerHTML = '';
      for (const c of candidatesAll) {
        const li = document.createElement('li');
        li.className = 'available-item';
        const left = document.createElement('div');
        left.style.flex = '1';
        const code = document.createElement('code');
        code.textContent = c.subnet;
        left.appendChild(code);
        const p = document.createElement('div');
        p.className = 'muted';
        p.style.marginTop = '6px';
        p.textContent = c.overlaps.length ? ('Conflicts with: ' + c.overlaps.join(', ')) : 'Available';
        left.appendChild(p);
        li.appendChild(left);
        const right = document.createElement('div');
        right.style.display = 'flex';
        right.style.gap = '8px';
        const badge = document.createElement('span');
        badge.className = 'code';
        badge.textContent = c.overlaps.length ? `conflict (${c.overlaps.length})` : 'ok';
        right.appendChild(badge);
        li.appendChild(right);
        debugList.appendChild(li);
      }

      availableCount.textContent = String(available.length);
      summary.textContent = available.length ? `Can allocate — ${available.length} available` : 'Cannot allocate';
      jsonPre.textContent = JSON.stringify({ available_subnets: available.map(x => x.subnet), candidates: candidatesAll }, null, 2);

      resultsContent.style.display = 'block';
      jsonSection.style.display = 'none';
      showSpinner(false);
    } catch (err) {
      showSpinner(false);
      showError(err.message || String(err));
    }
  }

  checkBtn.addEventListener('click', doCheck);

  copyAllBtn.addEventListener('click', async () => {
    const codes = Array.from(availableList.querySelectorAll('code')).map(n => n.textContent);
    if (codes.length === 0) return;
    await navigator.clipboard.writeText(codes.join('\n'));
    copyAllBtn.textContent = 'Copied';
    setTimeout(() => copyAllBtn.textContent = 'Copy all', 1200);
  });

  debugToggle.addEventListener('click', () => {
    const shown = debugSection.style.display !== 'none';
    debugSection.style.display = shown ? 'none' : 'block';
    debugToggle.textContent = shown ? 'Show conflicts (debug)' : 'Hide conflicts (debug)';
  });

  downloadJsonBtn.addEventListener('click', () => {
    const text = jsonPre.textContent || '{}';
    const blob = new Blob([text], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'subnet-check.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });

  // Run an initial check once loaded
  doCheck();
});