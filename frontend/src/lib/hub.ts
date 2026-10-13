// Tudo que o front precisa saber sobre o Twygo Hub fica aqui.
import axios from "axios";

export const HUB_URL = "https://hub.apps.twygo.com";

// Liga com VITE_HUB_BAR=1 (no build de produção ou no docker-compose).
export const hubBarLigada = import.meta.env.VITE_HUB_BAR === "1";

// Coloca a barra do Hub (link pro Hub, menu de apps, nome da pessoa e "Sair")
// no topo da página. Se der qualquer erro, a barra só não aparece.
export function carregarBarraDoHub() {
  const script = document.createElement("script");
  script.src = `${HUB_URL}/bar.js`;
  script.defer = true;
  document.head.appendChild(script);
}

// A API responde 401 quando está em AUTH_MODE=hub e o request não veio pelo Hub.
export function precisaEntrarPeloHub(erro: unknown): boolean {
  return axios.isAxiosError(erro) && erro.response?.status === 401;
}
