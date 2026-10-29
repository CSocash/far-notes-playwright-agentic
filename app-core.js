// Pure tracker logic shared by app.js (as window.FarNotesCore) and the node:test unit tests (via require).
// No DOM, network or global state: every input is a parameter.
(function (root) {
  const SECTION_NUMBER_PATTERN = /^\s*(\d+\.\d+)/;

  function sectionNumber(heading) {
    return heading.match(SECTION_NUMBER_PATTERN)?.[1];
  }

  function ecfrUrl(part, section, code = "") {
    const url = `https://www.ecfr.gov/current/title-14/part-${part}/section-${section}`;
    return code ? `${url}#p-${section}(${code})` : `${url}#section-${section}`;
  }

  // "91.103(a)", "91.5" for an entire-section item, or the heading itself when it has no section number.
  function referenceFor(heading, code) {
    const number = sectionNumber(heading);
    return number ? `${number}${code ? `(${code})` : ""}` : heading;
  }

  function normalizeQuery(value) {
    return value.trim().toLocaleLowerCase();
  }

  // filter is "all", "covered" or "uncovered"; query must already be normalized.
  function matchingSubsections(regulation, query, filter) {
    const regulationMatches = regulation.regulation.toLocaleLowerCase().includes(query);
    return regulation.subsections.filter((subsection) => {
      const matchesFilter = filter === "all" || (filter === "covered" ? subsection.covered : !subsection.covered);
      const text = `${referenceFor(regulation.regulation, subsection.code)} ${subsection.title} ${subsection.notes}`.toLocaleLowerCase();
      return matchesFilter && (!query || regulationMatches || text.includes(query));
    });
  }

  function summarize(subsections) {
    const total = subsections.length;
    const covered = subsections.filter((item) => item.covered).length;
    return {
      total,
      covered,
      remaining: total - covered,
      progress: total === 0 ? 0 : Math.round(covered / total * 100)
    };
  }

  // YYYY-MM-DD in the local time zone of the given moment (not UTC).
  function localDate(now = new Date()) {
    const offset = now.getTimezoneOffset();
    return new Date(now.getTime() - offset * 60_000).toISOString().slice(0, 10);
  }

  const core = { sectionNumber, ecfrUrl, referenceFor, normalizeQuery, matchingSubsections, summarize, localDate };
  if (typeof module !== "undefined" && module.exports) module.exports = core;
  else root.FarNotesCore = core;
})(typeof window !== "undefined" ? window : globalThis);
