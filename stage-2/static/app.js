"use strict";

import { api, escapeHTML, labelsFor, localToday, makeKey, readResponse, session, setKey, showMessage, token, user } from "/static/common.js";
import { markSelection, renderAvailability } from "/static/grid.js";

const app = document.querySelector("#app");
const state = { restaurants: [], restaurant: null, search: null, selection: null, sequence: 0, detailSequence: 0 };
function updateHeader() {
  const current = user();
  const tools = document.querySelector("[data-account-tools]");
  const authLink = document.querySelector("[data-nav-auth]");
  authLink.textContent = current ? "Your table" : "Sign in";
  authLink.href = current ? "/lookup" : "/login";
  if (current) {
    tools.innerHTML = `<span class="current-user" data-testid="current-user">Signed in as ${escapeHTML(current.display_name)}</span><button class="logout-button" data-testid="logout-button" type="button">Sign out</button>`;
  } else tools.innerHTML = "";
  document.querySelectorAll(".main-nav a").forEach(link => {
    if (link.getAttribute("href") === location.pathname) link.setAttribute("aria-current", "page");
  });
}

function renderHome() {
  app.innerHTML = `
    <section class="hero">
      <div class="hero-copy"><p class="eyebrow">A seat for the good part</p><h1>Find your place at the table.</h1><p>Choose an evening, gather your people, and we’ll find a table that feels just right.</p></div>
      <aside class="hero-note">A little planning leaves more room for the conversation.</aside>
    </section>
    <form class="card search-panel" id="search-form">
      <div class="field"><label for="restaurant-select">Restaurant</label><select id="restaurant-select" data-testid="restaurant-select" required><option value="">Loading restaurants…</option></select></div>
      <div class="field"><label for="date-input">Date</label><input id="date-input" data-testid="date-input" type="date" value="${localToday()}" required></div>
      <div class="field"><label for="party-size-input">Party size</label><input id="party-size-input" data-testid="party-size-input" type="number" min="1" step="1" value="2" required></div>
      <button class="button search-button" data-testid="search-button" type="submit">Find a table</button>
    </form>
    <div id="home-feedback"></div>
    <section id="availability-area" aria-live="polite"></section>
    <section id="booking-area"></section>`;
  updateHeader();
  loadRestaurants();
  document.querySelector("#search-form").addEventListener("submit", event => {
    event.preventDefault();
    searchFromInputs(false);
  });
}

async function loadRestaurants() {
  const select = document.querySelector("#restaurant-select");
  try {
    const data = await readResponse(await api("/restaurants"));
    state.restaurants = data.restaurants || [];
    if (!state.restaurants.length) {
      select.innerHTML = '<option value="">No restaurants are available yet</option>';
      select.disabled = true;
      showMessage(document.querySelector("#home-feedback"), "search-error", "Restaurant details will appear here when available.", "uncertain");
      return;
    }
    select.innerHTML = state.restaurants.map(restaurant => `<option value="${escapeHTML(restaurant.id)}">${escapeHTML(restaurant.name)}</option>`).join("");
    select.addEventListener("change", () => loadRestaurant(select.value));
    await loadRestaurant(select.value);
  } catch (error) {
    select.innerHTML = '<option value="">Restaurants could not be loaded</option>';
    select.disabled = true;
    showMessage(document.querySelector("#home-feedback"), "search-error", error.message, "error");
  }
}

async function loadRestaurant(id) {
  const requestId = ++state.detailSequence;
  try {
    const detail = await readResponse(await api(`/restaurants/${encodeURIComponent(id)}`));
    if (requestId === state.detailSequence) state.restaurant = detail;
  } catch (error) {
    if (requestId === state.detailSequence) showMessage(document.querySelector("#home-feedback"), "search-error", error.message);
  }
}

function searchFromInputs(preserveForm) {
  const restaurantId = document.querySelector("#restaurant-select").value;
  const date = document.querySelector("#date-input").value;
  const partySize = Number(document.querySelector("#party-size-input").value);
  if (!restaurantId || !date || !Number.isInteger(partySize) || partySize < 1) return;
  if (!preserveForm) {
    state.selection = null;
    document.querySelector("#booking-area").replaceChildren();
    showMessage(document.querySelector("#home-feedback"), "booking-error", "");
    showMessage(document.querySelector("#home-feedback"), "booking-uncertain", "");
  }
  const query = { restaurant_id: restaurantId, date, party_size: String(partySize) };
  runSearch(query, preserveForm).catch(error => {
    showMessage(document.querySelector("#home-feedback"), "search-error", error.message);
    document.querySelector("#availability-area").replaceChildren();
  });
}

async function runSearch(query, preserveForm) {
  const sequence = ++state.sequence;
  const area = document.querySelector("#availability-area");
  area.innerHTML = '<p class="status-line" role="status">Looking for a table…</p>';
  let restaurant;
  let result;
  try {
    const params = new URLSearchParams(query);
    restaurant = state.restaurant?.id === query.restaurant_id
      ? state.restaurant
      : await readResponse(await api(`/restaurants/${encodeURIComponent(query.restaurant_id)}`));
    result = await readResponse(await api(`/availability?${params}`));
  } catch (error) {
    if (sequence === state.sequence) throw error;
    return;
  }
  if (sequence !== state.sequence) return;
  state.restaurant = restaurant;
  state.search = { query, result, restaurant };
  renderAvailability(document.querySelector("#availability-area"), query, result, restaurant, chooseCell);
  if (preserveForm && state.selection) markSelection(state.selection);
}

function chooseCell(ids, time) {
  if (!user() || !token()) {
    showMessage(document.querySelector("#home-feedback"), "auth-error", "Sign in before confirming a table. Your search will stay here.");
    return;
  }
  if (!state.search) return;
  const startsAtLocal = `${state.search.query.date}T${time}`;
  state.selection = { ids, startsAtLocal, query: state.search.query, restaurant: state.search.restaurant };
  markSelection(state.selection);
  renderBookingForm();
  document.querySelector("#booking-area").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderBookingForm() {
  const selection = state.selection;
  const names = labelsFor(selection.restaurant, selection.ids);
  const summary = `${names.join(" + ")} · ${selection.startsAtLocal.replace("T", " at ")}`;
  document.querySelector("#booking-area").innerHTML = `<section class="card booking-panel" data-testid="booking-form"><div class="booking-panel-header"><div><p class="eyebrow">Make it yours</p><h2>Your table</h2><p data-testid="booking-summary">${escapeHTML(summary)}</p></div></div><form id="booking-submit-form"><div class="booking-grid"><div class="field"><label for="booking-party-size">Number of guests</label><input id="booking-party-size" data-testid="booking-party-size" type="number" min="1" step="1" value="${escapeHTML(selection.query.party_size)}" required></div><button class="button booking-submit" data-testid="booking-submit" type="submit">Confirm reservation</button></div></form><div id="booking-feedback"></div><div id="confirmation-area"></div></section>`;
  document.querySelector("#booking-submit-form").addEventListener("submit", submitBooking);
}

function pendingRequest(body) {
  let previous;
  try { previous = JSON.parse(session.get("pending-booking") || "null"); } catch { previous = null; }
  const same = previous && JSON.stringify(previous.body) === JSON.stringify(body);
  const pending = same ? previous : { body, key: makeKey() };
  session.set("pending-booking", JSON.stringify(pending));
  return pending;
}
function responseTables(response, selection) { return response.table_ids || (response.table_id ? [response.table_id] : selection.ids); }

async function submitBooking(event) {
  event.preventDefault();
  const selection = state.selection;
  const partySize = Number(document.querySelector("#booking-party-size").value);
  if (!selection || !Number.isInteger(partySize) || partySize < 1) return;
  const body = { restaurant_id: selection.restaurant.id, starts_at_local: selection.startsAtLocal, party_size: partySize };
  if (selection.ids.length === 1) body.table_id = selection.ids[0];
  else body.table_ids = selection.ids;
  const pending = pendingRequest(body);
  const feedback = document.querySelector("#booking-feedback");
  const confirmationArea = document.querySelector("#confirmation-area");
  feedback.replaceChildren();
  confirmationArea.replaceChildren();
  const submit = document.querySelector('[data-testid="booking-submit"]');
  submit.disabled = true;
  submit.textContent = "Confirming…";
  try {
    const response = await api("/reservations", { method: "POST", headers: { "Idempotency-Key": pending.key }, json: body });
    const result = await readResponse(response);
    if (typeof result.reference !== "string" || !result.reference) throw new Error("The reservation reply was incomplete. Please retry this same table.");
    showMessage(feedback, "booking-uncertain", "");
    showMessage(feedback, "booking-error", "");
    showConfirmation(result, responseTables(result, selection), selection);
  } catch (error) {
    if (error.status === 409 && error.code === "table_unavailable") {
      showMessage(feedback, "booking-error", error.message);
      runSearch(selection.query, true).catch(() => {});
    } else if (!error.status || error.status >= 500 || error instanceof SyntaxError) {
      showMessage(feedback, "booking-uncertain", "We could not confirm whether that request reached the restaurant. Retry this unchanged request to check safely.", "uncertain");
    } else {
      showMessage(feedback, "booking-error", error.message);
    }
  } finally {
    submit.disabled = false;
    submit.textContent = "Confirm reservation";
  }
}

function showConfirmation(result, ids, selection) {
  const area = document.querySelector("#confirmation-area");
  const labels = labelsFor(selection.restaurant, ids);
  area.innerHTML = `<section class="confirmation" data-testid="confirmation" aria-live="polite"><div class="confirmation-top"><h3>We’ll save you a seat</h3><span class="confirmation-reference" data-testid="confirmation-reference"></span></div><p data-testid="confirmation-tables">Tables: ${escapeHTML(labels.join(" + "))}</p><p data-testid="confirmation-details">${escapeHTML(selection.restaurant.name)} · ${escapeHTML(labels.join(" + "))} · ${escapeHTML(selection.startsAtLocal.replace("T", " at "))}</p></section>`;
  area.querySelector('[data-testid="confirmation-reference"]').textContent = result.reference;
}

function renderAuth(kind) {
  const signup = kind === "signup";
  const title = signup ? "A table starts here." : "Welcome back.";
  app.innerHTML = `<section class="auth-layout"><div class="card auth-card"><p class="eyebrow">${signup ? "Join us" : "Your evening awaits"}</p><h1>${title}</h1><p class="hint">${signup ? "Create an account to keep your reservation close." : "Sign in to book or manage your reservation."}</p><form id="auth-form">${signup ? '<div class="field"><label for="signup-display-name">Name</label><input id="signup-display-name" data-testid="signup-display-name" name="display_name" autocomplete="name" required></div>' : ""}<div class="field"><label for="${signup ? "signup-email" : "login-email"}">Email</label><input id="${signup ? "signup-email" : "login-email"}" data-testid="${signup ? "signup-email" : "login-email"}" name="email" type="email" autocomplete="email" required></div><div class="field"><label for="${signup ? "signup-password" : "login-password"}">Password</label><input id="${signup ? "signup-password" : "login-password"}" data-testid="${signup ? "signup-password" : "login-password"}" name="password" type="password" autocomplete="${signup ? "new-password" : "current-password"}" required></div><div id="auth-feedback"></div><button class="button" data-testid="${signup ? "signup-submit" : "login-submit"}" type="submit">${signup ? "Create account" : "Sign in"}</button></form><p class="auth-switch">${signup ? 'Already have an account? <a href="/login">Sign in</a>' : 'New to Tablekeeper? <a href="/signup">Create an account</a>'}</p></div></section>`;
  updateHeader();
  document.querySelector("#auth-form").addEventListener("submit", event => submitAuth(event, signup));
}

async function submitAuth(event, signup) {
  event.preventDefault();
  const form = new FormData(event.currentTarget);
  const body = { email: form.get("email"), password: form.get("password") };
  const name = signup ? form.get("display_name") : null;
  if (signup) body.display_name = name;
  const button = event.currentTarget.querySelector("button");
  button.disabled = true;
  try {
    const result = await readResponse(await api(signup ? "/auth/signup" : "/auth/login", { method: "POST", json: body }));
    session.set("token", result.token);
    session.set("user", JSON.stringify({ user_id: result.user_id, display_name: result.display_name }));
    location.assign("/");
  } catch (error) {
    showMessage(document.querySelector("#auth-feedback"), "auth-error", error.message);
  } finally { button.disabled = false; }
}

function renderLookup() {
  app.innerHTML = `<section class="lookup-layout"><div class="card lookup-card"><p class="eyebrow">Keep the details close</p><h1>Find your reservation.</h1><p class="hint">Enter the reference from your confirmation. Sign in with the account that made the booking.</p><form class="lookup-form" id="lookup-form"><div class="field"><label for="lookup-reference">Reservation reference</label><input id="lookup-reference" data-testid="lookup-reference-input" autocomplete="off" spellcheck="false" required></div><button class="button" data-testid="lookup-submit" type="submit">Look it up</button></form><div id="lookup-feedback"></div><div id="reservation-area"></div></div></section>`;
  updateHeader();
  document.querySelector("#lookup-form").addEventListener("submit", lookupReservation);
}

async function lookupReservation(event) {
  event.preventDefault();
  const reference = document.querySelector("#lookup-reference").value.trim();
  const area = document.querySelector("#reservation-area");
  area.replaceChildren();
  showMessage(document.querySelector("#lookup-feedback"), "reservation-error", "");
  if (!user() || !token()) {
    showMessage(document.querySelector("#lookup-feedback"), "reservation-error", "Sign in to look up a reservation.");
    return;
  }
  try {
    const reservation = await readResponse(await api(`/reservations/${encodeURIComponent(reference)}`));
    const restaurant = await readResponse(await api(`/restaurants/${encodeURIComponent(reservation.restaurant_id)}`));
    renderReservation(reservation, restaurant);
    showMessage(document.querySelector("#lookup-feedback"), "reservation-error", "");
  } catch (error) {
    showMessage(document.querySelector("#lookup-feedback"), "reservation-error", error.message);
  }
}

function renderReservation(reservation, restaurant) {
  const area = document.querySelector("#reservation-area");
  const ids = reservation.table_ids || (reservation.table_id ? [reservation.table_id] : []);
  const labels = labelsFor(restaurant, ids);
  const start = reservation.starts_at_local || "";
  area.innerHTML = `<section class="card reservation-detail" data-testid="reservation-detail"><p class="eyebrow">${escapeHTML(restaurant.name)}</p><h2>Reservation ${escapeHTML(reservation.reference)}</h2><dl class="reservation-meta"><div><dt>Status</dt><dd class="reservation-status ${reservation.status === "cancelled" ? "status-cancelled" : "status-confirmed"}" data-testid="reservation-status">${escapeHTML(reservation.status)}</dd></div><div><dt>When</dt><dd>${escapeHTML(start.replace("T", " at "))}</dd></div><div><dt>Seating</dt><dd data-testid="reservation-tables">${escapeHTML(labels.join(" + "))}</dd></div><div><dt>Party</dt><dd>${escapeHTML(reservation.party_size)}</dd></div></dl><div id="cancel-feedback"></div>${reservation.status === "confirmed" ? '<button class="button button-secondary" data-testid="reservation-cancel-button" type="button">Cancel reservation</button>' : ""}</section>`;
  const cancel = area.querySelector('[data-testid="reservation-cancel-button"]');
  if (cancel) cancel.addEventListener("click", () => cancelReservation(reservation.reference, restaurant));
}

async function cancelReservation(reference, restaurant) {
  const button = document.querySelector('[data-testid="reservation-cancel-button"]');
  button.disabled = true;
  try {
    const reservation = await readResponse(await api(`/reservations/${encodeURIComponent(reference)}/cancel`, { method: "POST" }));
    renderReservation(reservation, restaurant);
  } catch (error) {
    showMessage(document.querySelector("#cancel-feedback"), "reservation-error", error.message);
    button.disabled = false;
  }
}

document.addEventListener("focusin", event => {
  if (event.target instanceof HTMLElement && event.target.matches("a, button, input, select, textarea")) {
    event.target.classList.add("control-focused");
  }
});
document.addEventListener("focusout", event => {
  if (event.target instanceof HTMLElement) event.target.classList.remove("control-focused");
});
document.addEventListener("click", event => {
  if (event.target.matches('[data-testid="logout-button"]')) {
    session.remove("token");
    session.remove("user");
    location.assign("/");
  }
});

const path = location.pathname;
if (path === "/signup") renderAuth("signup");
else if (path === "/login") renderAuth("login");
else if (path === "/lookup") renderLookup();
else renderHome();
app.setAttribute("aria-busy", "false");
