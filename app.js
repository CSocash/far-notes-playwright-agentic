const { sectionNumber, ecfrUrl, referenceFor, normalizeQuery, matchingSubsections, summarize, localDate } = window.FarNotesCore;

let regulations = [];
let activeFilter = "all";
let activePart = "91";
let loadSequence = 0;
let toastTimer;
// Sections start collapsed. expandedSections holds the ids the user opened. While a search is active,
// sections with matches open automatically, and searchCollapsed holds the ones closed during that search.
let expandedSections = new Set();
let searchCollapsed = new Set();
const saveTimers = new Map();
const saveQueues = new Map();

const rows = document.querySelector("#regulation-rows");
const rowTemplate = document.querySelector("#row-template");
const searchInput = document.querySelector("#search");
const partSelect = document.querySelector("#part-select");

async function apiRequest(path, options = {}) {
  const response = await FarNotesApi.fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers }
  });
  const result = await response.json();
  if (response.status === 401 && !path.startsWith("/api/auth/")) {
    FarNotesApi.goTo("/login");
  }
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status}).`);
  return result;
}

function subsectionItems() {
  return regulations.flatMap((regulation) => regulation.subsections);
}

function makeSectionRow(regulation, expanded) {
  const row = document.createElement("tr");
  row.className = "section-row";
  row.setAttribute("role", "row");
  row.dataset.sectionId = regulation.id;
  const cell = document.createElement("td");
  cell.setAttribute("role", "cell");
  cell.colSpan = 4;

  const header = document.createElement("div");
  header.className = "section-row-content";
  const toggle = document.createElement("button");
  toggle.className = "section-toggle";
  toggle.type = "button";
  toggle.setAttribute("aria-expanded", String(expanded));
  toggle.setAttribute("aria-label", `Study items in ${regulation.regulation}`);
  toggle.addEventListener("click", () => toggleSection(regulation));
  const headingNumber = sectionNumber(regulation.regulation);
  const headingLink = document.createElement("a");
  headingLink.className = "section-heading-link";
  headingLink.textContent = regulation.regulation;
  headingLink.target = "_blank";
  headingLink.rel = "noopener noreferrer";
  headingLink.setAttribute("aria-label", `Open ${regulation.regulation} in the eCFR in a new tab`);
  if (headingNumber) {
    headingLink.href = ecfrUrl(regulation.partId, headingNumber);
  } else {
    headingLink.removeAttribute("href");
  }

  const input = document.createElement("input");
  input.className = "regulation-input";
  input.value = regulation.regulation;
  input.setAttribute("aria-label", "Regulation section");
  input.hidden = true;
  let headingBeforeEdit = regulation.regulation;
  input.addEventListener("focus", () => {
    headingBeforeEdit = regulation.regulation;
  });
  input.addEventListener("input", () => {
    regulation.regulation = input.value;
    queueSave(regulation, "regulation");
  });
  input.addEventListener("blur", () => {
    input.value = regulation.regulation;
    queueSave(regulation, "regulation", true);
    headingLink.textContent = regulation.regulation;
    headingLink.setAttribute("aria-label", `Open ${regulation.regulation} in the eCFR in a new tab`);
    const updatedSectionNumber = sectionNumber(regulation.regulation);
    if (updatedSectionNumber) headingLink.href = ecfrUrl(regulation.partId, updatedSectionNumber);
    else headingLink.removeAttribute("href");
    editButton.setAttribute("aria-label", `Edit section heading ${regulation.regulation}`);
    toggle.setAttribute("aria-label", `Study items in ${regulation.regulation}`);
    input.hidden = true;
    headingLink.hidden = false;
  });
  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") input.blur();
    if (event.key === "Escape") {
      regulation.regulation = headingBeforeEdit;
      input.value = headingBeforeEdit;
      input.blur();
    }
  });

  const editButton = document.createElement("button");
  editButton.className = "edit-button";
  editButton.type = "button";
  editButton.textContent = "Edit";
  editButton.hidden = regulation.isLocked;
  editButton.setAttribute("aria-label", `Edit section heading ${regulation.regulation}`);
  editButton.addEventListener("click", () => {
    headingLink.hidden = true;
    input.hidden = false;
    input.focus();
    input.select();
  });

  const progress = document.createElement("span");
  progress.className = "section-progress";
  renderSectionProgress(progress, regulation);

  header.append(toggle, headingLink, input, editButton, progress);
  cell.append(header);
  row.append(cell);
  return row;
}

function makeSubsectionRow(regulation, subsection) {
  const fragment = rowTemplate.content.cloneNode(true);
  const row = fragment.querySelector("tr");
  const headingNumber = sectionNumber(regulation.regulation);
  const reference = row.querySelector(".subsection-reference");
  const title = row.querySelector(".subsection-title");
  const subsectionReference = referenceFor(regulation.regulation, subsection.code);
  const link = document.createElement("a");
  link.className = "subsection-reference";
  link.textContent = subsectionReference;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.setAttribute("aria-label", `Open ${subsectionReference} in the eCFR in a new tab`);
  if (headingNumber) link.href = ecfrUrl(regulation.partId, headingNumber, subsection.code);
  reference.replaceWith(link);
  title.textContent = subsection.title;
  title.hidden = !subsection.title;

  const coveredInput = row.querySelector(".covered-input");
  const coveredLabel = row.querySelector(".covered-label");
  const dateInput = row.querySelector(".date-input");
  const notesInput = row.querySelector(".notes-input");
  coveredInput.checked = subsection.covered;
  coveredLabel.textContent = subsection.covered ? "Yes" : "No";
  coveredInput.setAttribute("aria-label", `Mark ${subsectionReference} as covered`);
  coveredInput.addEventListener("change", () => {
    subsection.covered = coveredInput.checked;
    subsection.date = subsection.covered ? localDate() : "";
    dateInput.value = subsection.date;
    coveredLabel.textContent = subsection.covered ? "Yes" : "No";
    queueSave(subsection, "subsection", true);
    updateSummary();
    updateSectionProgress(regulation);
    if (activeFilter !== "all") render();
  });
  dateInput.value = subsection.date;
  dateInput.setAttribute("aria-label", `Date covered for ${subsectionReference}`);
  dateInput.addEventListener("change", () => {
    subsection.date = dateInput.value;
    queueSave(subsection, "subsection", true);
  });
  notesInput.value = subsection.notes;
  notesInput.setAttribute("aria-label", `Notes for ${subsectionReference}`);
  notesInput.addEventListener("input", () => {
    subsection.notes = notesInput.value;
    queueSave(subsection, "subsection");
  });
  notesInput.addEventListener("blur", () => queueSave(subsection, "subsection", true));
  return fragment;
}

function renderSectionProgress(element, regulation) {
  const { total, covered } = summarize(regulation.subsections);
  const label = document.createElement("span");
  label.className = "sr-only";
  label.textContent = " covered";
  element.replaceChildren(`${covered}/${total}`, label);
}

function updateSectionProgress(regulation) {
  const element = rows.querySelector(`[data-section-id="${regulation.id}"] .section-progress`);
  if (element) renderSectionProgress(element, regulation);
}

function isExpanded(regulation, query) {
  return query ? !searchCollapsed.has(regulation.id) : expandedSections.has(regulation.id);
}

function toggleSection(regulation) {
  // During a search, searchCollapsed records closed sections; otherwise expandedSections records open ones.
  const sections = normalizeQuery(searchInput.value) ? searchCollapsed : expandedSections;
  if (sections.has(regulation.id)) sections.delete(regulation.id);
  else sections.add(regulation.id);
  render();
  rows.querySelector(`[data-section-id="${regulation.id}"] .section-toggle`)?.focus();
}

function setAllSections(expand) {
  const ids = regulations.map((regulation) => regulation.id);
  if (normalizeQuery(searchInput.value)) searchCollapsed = new Set(expand ? [] : ids);
  else expandedSections = new Set(expand ? ids : []);
  render();
}

function render() {
  const query = normalizeQuery(searchInput.value);
  const visibleRegulations = regulations
    .map((regulation) => ({
      regulation,
      subsections: matchingSubsections(regulation, query, activeFilter)
    }))
    .filter((group) => group.subsections.length > 0);

  rows.replaceChildren();
  let visibleCount = 0;
  for (const group of visibleRegulations) {
    const expanded = isExpanded(group.regulation, query);
    rows.append(makeSectionRow(group.regulation, expanded));
    for (const subsection of group.subsections) {
      if (expanded) rows.append(makeSubsectionRow(group.regulation, subsection));
      visibleCount += 1;
    }
  }

  document.querySelector("#empty-state").hidden = visibleCount > 0;
  document.querySelector("table").hidden = visibleCount === 0;
  updateVisibleCount(visibleCount);
  updateSummary();
}

function updateVisibleCount(visibleCount) {
  const total = subsectionItems().length;
  document.querySelector("#results-count").textContent = `Showing ${visibleCount} of ${total} study items`;
}

function updateSummary() {
  const { total, covered, remaining, progress } = summarize(subsectionItems());
  document.querySelector("#total-count").textContent = total;
  document.querySelector("#covered-count").textContent = covered;
  document.querySelector("#remaining-count").textContent = remaining;
  document.querySelector("#filter-all-count").textContent = total;
  document.querySelector("#filter-uncovered-count").textContent = remaining;
  document.querySelector("#filter-covered-count").textContent = covered;
  document.querySelector("#progress-percent").textContent = `${progress}%`;
  document.querySelector("#progress-count").textContent = `${covered} of ${total} study items covered`;
  document.querySelector("#progress-bar").style.width = `${progress}%`;
}

function saveKey(item, type) {
  return `${type}:${item.id}`;
}

function queueSave(item, type, immediate = false) {
  const key = saveKey(item, type);
  clearTimeout(saveTimers.get(key));
  if (!immediate) {
    saveTimers.set(key, setTimeout(() => persistItem(item, type), 350));
    return;
  }
  persistItem(item, type);
}

function persistItem(item, type) {
  const key = saveKey(item, type);
  clearTimeout(saveTimers.get(key));
  saveTimers.delete(key);
  const path = type === "regulation"
    ? `/api/regulations/${item.id}?part=${item.partId}`
    : `/api/subsections/${item.id}?part=${item.partId}`;
  const body = type === "regulation"
    ? { regulation: item.regulation }
    : { covered: item.covered, date: item.date, notes: item.notes };
  const previous = saveQueues.get(key) || Promise.resolve();
  const operation = previous
    .catch(() => {})
    .then(() => apiRequest(path, { method: "PATCH", body: JSON.stringify(body) }))
    .catch((error) => {
      console.error(`Unable to save ${type} ${item.id}.`, error);
      showToast(`Could not save ${type === "regulation" ? "section" : "study item"}: ${error.message}`);
    })
    .finally(() => {
      if (saveQueues.get(key) === operation) saveQueues.delete(key);
    });
  saveQueues.set(key, operation);
  return operation;
}

async function addRegulation() {
  try {
    const regulation = await apiRequest(`/api/regulations?part=${activePart}`, {
      method: "POST",
      body: JSON.stringify({ regulation: "" })
    });
    regulation.subsections.forEach((subsection) => {
      subsection.partId = activePart;
    });
    regulation.partId = activePart;
    regulations.push(regulation);
    expandedSections.add(regulation.id);
    activeFilter = "all";
    document.querySelectorAll(".filter-button").forEach((button) => {
      button.classList.toggle("is-active", button.dataset.filter === activeFilter);
    });
    searchInput.value = "";
    render();
    rows.lastElementChild?.previousElementSibling?.querySelector(".regulation-input")?.focus();
    showToast("New section added. Enter a regulation number to get started.");
  } catch (error) {
    console.error("Unable to add a regulation.", error);
    showToast(`Could not add section: ${error.message}`);
  }
}

function showToast(message) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.add("is-visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("is-visible"), 2400);
}

document.querySelector("#add-regulation").addEventListener("click", addRegulation);
document.querySelector("#logout").addEventListener("click", async () => {
  try {
    await apiRequest("/api/auth/logout", { method: "POST" });
    FarNotesApi.goTo("/login");
  } catch (error) {
    console.error("Unable to sign out.", error);
    showToast(`Could not sign out: ${error.message}`);
  }
});
partSelect.addEventListener("change", () => {
  activeFilter = "all";
  document.querySelectorAll(".filter-button").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.filter === activeFilter);
  });
  searchInput.value = "";
  loadPart(partSelect.value);
});

searchInput.addEventListener("input", () => {
  searchCollapsed = new Set();
  render();
});
document.querySelector("#expand-all").addEventListener("click", () => setAllSections(true));
document.querySelector("#collapse-all").addEventListener("click", () => setAllSections(false));
document.querySelectorAll(".filter-button").forEach((button) => {
  button.addEventListener("click", () => {
    activeFilter = button.dataset.filter;
    document.querySelectorAll(".filter-button").forEach((filterButton) => {
      filterButton.classList.toggle("is-active", filterButton === button);
    });
    render();
  });
});
document.addEventListener("keydown", (event) => {
  if (event.key === "/" && !["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) {
    event.preventDefault();
    searchInput.focus();
  }
  if (event.key === "Escape" && document.activeElement === searchInput) {
    searchInput.value = "";
    render();
    searchInput.blur();
  }
});

async function loadPart(partId) {
  const sequence = ++loadSequence;
  activePart = partId;
  regulations = [];
  expandedSections = new Set();
  searchCollapsed = new Set();
  document.querySelector("#brand-part").textContent = `PART ${partId}`;
  document.querySelector(".brand").setAttribute("aria-label", `Part ${partId} Study Log home`);
  document.querySelector("#intro-copy").textContent =
    `A simple place to track your progress through the FAA's Part ${partId} regulations. One section at a time.`;
  document.title = `Part ${partId} Study Log`;
  document.querySelector("#connection-status").innerHTML = '<span class="status-dot"></span> Loading regulations...';
  render();
  try {
    const result = await apiRequest(`/api/regulations?part=${partId}`);
    if (sequence !== loadSequence) return;
    regulations = result.map((regulation) => ({
      ...regulation,
      partId,
      subsections: regulation.subsections.map((subsection) => ({ ...subsection, partId }))
    }));
    document.querySelector("#connection-status").innerHTML = '<span class="status-dot"></span> Connected to SQLite';
    document.querySelector("#empty-state").querySelector("strong").textContent = "No study items found";
    document.querySelector("#empty-state").querySelector("span:last-child").textContent =
      "Try another search, or add a regulation section to your list.";
    render();
  } catch (error) {
    if (sequence !== loadSequence) return;
    console.error(`Unable to connect to the Part ${partId} database.`, error);
    const emptyState = document.querySelector("#empty-state");
    emptyState.querySelector("strong").textContent = "Database connection unavailable";
    emptyState.querySelector("span:last-child").textContent = "Start the website with npm start, then reload this page.";
    emptyState.hidden = false;
    document.querySelector("table").hidden = true;
    document.querySelector("#connection-status").innerHTML = '<span class="status-dot status-dot-error"></span> Database unavailable';
    showToast(`Could not load regulations: ${error.message}`);
  }
}

apiRequest("/api/auth/me")
  .then((user) => {
    if (!user.authenticated) {
      FarNotesApi.goTo("/login");
      return;
    }
    document.querySelector("#current-user").textContent = user.username;
    loadPart(activePart);
  })
  .catch((error) => {
    console.error("Unable to verify the signed-in account.", error);
    FarNotesApi.goTo("/login");
  });
