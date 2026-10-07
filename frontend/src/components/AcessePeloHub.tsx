import { HUB_URL } from "../lib/hub";

// Tela mostrada quando a API diz que a pessoa não está logada (401).
export function AcessePeloHub() {
  return (
    <div className="hub-aviso">
      <h2>Acesse pelo Twygo Hub</h2>
      <p>Este app usa o login do Twygo Hub. Entre pelo Hub e abra o app de lá.</p>
      <a href={HUB_URL}>Ir para o Twygo Hub</a>
    </div>
  );
}
