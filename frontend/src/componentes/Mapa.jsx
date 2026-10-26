// Mapa interactivo com OpenStreetMap (UC07, CT04).
// Se o serviço de mapas falhar (sem internet ou limite de pedidos), mostra
// apenas o endereço textual e avisa o utilizador (TC08, TC34, RNF09).
import { useRef, useState } from "react";
import { CircleMarker, MapContainer, TileLayer, Tooltip, useMapEvents } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import Icone from "./Icone";

const CORES = { Escola: "#0A3D62", Mercado: "#B45309", Transporte: "#5B6573", "Saúde": "#15803D" };

function DetectarFalhas({ aoFalhar }) {
  // Conta os mosaicos (tiles) que não carregam; a partir de 3 falhas desiste
  const falhas = useRef(0);
  return (
    <TileLayer
      attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
      url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      eventHandlers={{ tileerror: () => { falhas.current += 1; if (falhas.current >= 3) aoFalhar(); } }}
    />
  );
}

function Clicar({ aoClicar }) {
  useMapEvents({ click: (e) => aoClicar?.(e.latlng) });
  return null;
}

export default function Mapa({ latitude, longitude, endereco, pontos = [], aoClicar, zoom = 15, altura }) {
  const [falhou, setFalhou] = useState(typeof navigator !== "undefined" && navigator.onLine === false);

  if (falhou)
    return (
      <div className="aviso-bloco" role="status">
        <Icone nome="mapa" />
        <div>
          <strong>Mapa indisponível neste momento.</strong>
          <p>{endereco || `Coordenadas: ${Number(latitude).toFixed(5)}, ${Number(longitude).toFixed(5)}`}</p>
        </div>
      </div>
    );

  return (
    <MapContainer center={[latitude, longitude]} zoom={zoom} className="mapa" style={altura ? { height: altura } : undefined}
                  scrollWheelZoom={false} key={`${latitude},${longitude}`}>
      <DetectarFalhas aoFalhar={() => setFalhou(true)} />
      <Clicar aoClicar={aoClicar} />
      <CircleMarker center={[latitude, longitude]} radius={11} pathOptions={{ color: "#fff", weight: 3, fillColor: "#B91C1C", fillOpacity: 1 }}>
        <Tooltip>{endereco || "Imóvel"}</Tooltip>
      </CircleMarker>
      {pontos.map((p) => (
        <CircleMarker key={p.nome} center={[p.latitude, p.longitude]} radius={7}
                      pathOptions={{ color: "#fff", weight: 2, fillColor: CORES[p.categoria] || "#0A3D62", fillOpacity: 1 }}>
          <Tooltip>{p.categoria}: {p.nome} ({p.distancia_km} km)</Tooltip>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
