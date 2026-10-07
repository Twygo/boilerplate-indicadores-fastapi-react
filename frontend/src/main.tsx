import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { carregarBarraDoHub, hubBarLigada } from "./lib/hub";

if (hubBarLigada) carregarBarraDoHub();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
