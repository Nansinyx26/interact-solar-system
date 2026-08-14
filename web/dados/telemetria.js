import { URL_SERVIDOR_RENDER } from "../config.js";

const ENDPOINT_TELEMETRIA = "/api/telemetria";

export function registrarSessaoWeb() {
  if (typeof fetch !== "function") return;
  const payload = JSON.stringify({ evento: "sessao", origem: "web" });

  fetch(ENDPOINT_TELEMETRIA, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
  }).catch(() => {
    if (URL_SERVIDOR_RENDER) {
      fetch(`${URL_SERVIDOR_RENDER}/api/telemetria`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      }).catch(() => {});
    }
  });
}

export function registrarInteracaoWeb(corpo, gesto = null) {
  if (typeof fetch !== "function" || !corpo) return;
  const payload = JSON.stringify({ evento: "interacao", corpo, gesto, origem: "web" });

  fetch(ENDPOINT_TELEMETRIA, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: payload,
  }).catch(() => {
    if (URL_SERVIDOR_RENDER) {
      fetch(`${URL_SERVIDOR_RENDER}/api/telemetria`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
      }).catch(() => {});
    }
  });
}
