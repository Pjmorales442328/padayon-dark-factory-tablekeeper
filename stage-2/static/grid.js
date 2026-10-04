import { escapeHTML, labelsFor, setKey } from "/static/common.js";

export function renderAvailability(area, query, result, restaurant, choose) {
  if (!result.slots?.length) {
    area.innerHTML = '<div class="section-heading"><div><p class="eyebrow">Your evening</p><h2>Availability</h2></div></div><div class="empty-state" data-testid="no-slots"><h3>A quiet day</h3><p>This restaurant is closed on that date. Try another day.</p></div>';
    return;
  }
  const tables = restaurant.tables || [];
  const tableMap = new Map(tables.map(table => [table.id, table]));
  const pairs = (restaurant.combinable || []).filter(pair => Array.isArray(pair) && pair.length === 2 && pair.every(id => tableMap.has(id)) && pair[0] !== pair[1]);
  const rows = result.slots.map(slot => renderSlot(slot, query, restaurant, tables, tableMap, pairs));
  area.innerHTML = `<div class="section-heading"><div><p class="eyebrow">${escapeHTML(restaurant.name)}</p><h2>Choose a time</h2><p>${escapeHTML(query.date)} · party of ${escapeHTML(query.party_size)}</p></div></div><div class="availability-list" data-testid="availability-grid">${rows.join("")}</div>`;
  area.querySelectorAll(".slot-cell").forEach(button => {
    button.addEventListener("click", () => {
      if (button.dataset.available === "true") choose(JSON.parse(decodeURIComponent(button.dataset.ids)), button.dataset.time);
    });
  });
}

function renderSlot(slot, query, restaurant, tables, tableMap, pairs) {
  const time = slot.starts_at_local.slice(11, 16);
  const singles = new Set(slot.available_table_ids || []);
  const options = new Set((slot.available_options || []).map(option => setKey(option.table_ids || [])));
  const cells = tables.map(table => cellMarkup([table.id], time, table.capacity, singles.has(table.id), restaurant));
  pairs.forEach(pair => {
    const capacity = pair.reduce((sum, id) => sum + tableMap.get(id).capacity, 0);
    if (capacity >= Number(query.party_size)) cells.push(cellMarkup(pair, time, capacity, options.has(setKey(pair)), restaurant));
  });
  return `<article class="slot-row"><time class="slot-time" datetime="${escapeHTML(slot.starts_at)}">${escapeHTML(time)}</time><div class="slot-options">${cells.join("")}</div></article>`;
}

function cellMarkup(ids, time, capacity, available, restaurant) {
  const names = labelsFor(restaurant, ids);
  const label = ids.length === 1 ? names[0] : `Together: ${names.join(" + ")}`;
  const state = available ? "Available" : "Reserved";
  const encodedIds = encodeURIComponent(JSON.stringify(ids));
  return `<button class="slot-cell" type="button" data-testid="slot-${escapeHTML(ids.join("+"))}-${escapeHTML(time)}" data-ids="${encodedIds}" data-time="${escapeHTML(time)}" data-available="${available}" aria-pressed="false" aria-label="${escapeHTML(`${label}, ${time}, ${state}`)}"><span class="slot-label">${escapeHTML(label)}</span><span class="slot-capacity">Seats up to ${capacity}</span><span class="slot-state">${state}</span></button>`;
}

export function markSelection(selection) {
  if (!selection) return;
  const id = `slot-${selection.ids.join("+")}-${selection.startsAtLocal.slice(11)}`;
  const cell = [...document.querySelectorAll(".slot-cell")].find(button => button.dataset.testid === id);
  document.querySelectorAll(".slot-cell").forEach(button => button.setAttribute("aria-pressed", String(button === cell)));
}
