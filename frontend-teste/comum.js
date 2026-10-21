// Funções compartilhadas da interface de teste.
const API = location.origin; // a interface é servida pela própria API em /teste

function token() { return localStorage.getItem("amparapet_token"); }

async function api(caminho, opcoes = {}) {
  const headers = opcoes.headers || {};
  if (token()) headers["Authorization"] = "Bearer " + token();
  if (opcoes.json !== undefined) {
    headers["Content-Type"] = "application/json";
    opcoes.body = JSON.stringify(opcoes.json);
  }
  const resp = await fetch(API + caminho, { ...opcoes, headers });
  if (resp.status === 204) return null;
  const dados = await resp.json().catch(() => null);
  if (!resp.ok) {
    let msg = dados && dados.detail;
    if (Array.isArray(msg)) msg = msg.map(e => `${e.loc.slice(1).join(".")}: ${e.msg}`).join("\n");
    const erro = new Error(msg || resp.statusText);
    erro.status = resp.status;
    throw erro;
  }
  return dados;
}

let OPCOES = null;
async function opcoes() { return OPCOES ||= await api("/api/opcoes"); }
function rotulo(tipo, valor) { return (OPCOES && OPCOES[tipo][valor]) || valor; }
function simNao(v) { return v ? "Sim" : "Não"; }
function esc(t) { return String(t ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

function nav() {
  document.body.insertAdjacentHTML("afterbegin", `
    <div class="aviso">Interface simples apenas para TESTAR a API. Documentação completa: <a href="/docs">/docs</a></div>
    <nav>
      <a href="index.html">Vitrine</a>
      <a href="como-adotar.html">Como adotar</a>
      <a href="admin.html">Área administrativa</a>
      <a href="/docs">API (Swagger)</a>
    </nav>`);
}

async function rodape() {
  const a = await api("/api/abrigo");
  document.body.insertAdjacentHTML("beforeend",
    `<footer><b>${esc(a.nome_abrigo)}</b>\n${esc(a.endereco)} — ${esc(a.cidade)}\n${esc(a.horario_funcionamento)}</footer>`);
  return a;
}
