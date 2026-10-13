/// <reference types="vite/client" />

interface ImportMetaEnv {
  // "1" = carrega a barra do Twygo Hub no topo da tela (ver src/lib/hub.ts)
  readonly VITE_HUB_BAR?: string;
}
