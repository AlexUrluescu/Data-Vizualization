"use client";
import React, { useEffect, useRef, useState } from "react";
import ChatWithAI from "./chat-ai";

// Types
interface StreetData {
  name: string;
  coordinates: [number, number][];
  carCount: number;
  color: string;
  length?: number;
  density?: number;
  osmId?: number;
  type?: string;
}

const mockStreetData: StreetData[] = [
  {
    name: "Bulevardul Corneliu Coposu",
    coordinates: [
      [45.79178, 24.14986],
      [45.7927, 24.15157],
      [45.79384, 24.15385],
      [45.79485, 24.15562],
      [45.79534, 24.15677],
      [45.79607, 24.15824],
      [45.79633, 24.1591],
      [45.79715, 24.16072],
      [45.79838, 24.16287],
      [45.7988, 24.16361],
    ],
    carCount: 78,
    color: "#cc0000",
  },
  {
    name: "Strada Bastionului",
    coordinates: [
      [45.7936, 24.14461],
      [45.79419, 24.14503],
      [45.79482, 24.14541],
      [45.79512, 24.14569],
      [45.79536, 24.146],
    ],
    carCount: 1000,
    color: "#88cc44",
  },
  {
    name: "Strada Emil Cioran",
    coordinates: [
      [45.78957, 24.14665],
      [45.7899, 24.14695],
      [45.79018, 24.14714],
      [45.79061, 24.14779],
    ],
    carCount: 5,
    color: "#44dd44",
  },
  {
    name: "Strada Mitropoliei",
    coordinates: [
      [45.7935, 24.14614],
      [45.79433, 24.14688],
      [45.79559, 24.1487],
      [45.79697, 24.15007],
    ],
    carCount: 34,
    color: "#ff8844",
  },
];

// Haversine formula for street length
const calculateStreetLength = (coordinates: [number, number][]): number => {
  let totalLength = 0;
  for (let i = 0; i < coordinates.length - 1; i++) {
    const [lat1, lon1] = coordinates[i];
    const [lat2, lon2] = coordinates[i + 1];
    const R = 6371;
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) ** 2 +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) ** 2;
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    totalLength += R * c;
  }
  return totalLength;
};

// Traffic color based on density
const getColorForTrafficDensity = (
  carCount: number,
  length: number
): string => {
  if (length === 0) return "#888888";
  const density = carCount / length;
  if (density >= 400) return "#cc0000";
  if (density >= 250) return "#ff4444";
  if (density >= 150) return "#ffaa44";
  if (density >= 80) return "#88cc44";
  return "#44dd44";
};

const getTrafficLevel = (density: number): string => {
  if (density >= 400) return "Very Heavy";
  if (density >= 250) return "Heavy";
  if (density >= 150) return "Medium";
  if (density >= 80) return "Moderate";
  return "Light";
};

declare global {
  interface Window {
    L: any;
  }
}

const SibiuTrafficMap: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [currentHour, setCurrentHour] = useState<number>(new Date().getHours());
  const [selectedStreet, setSelectedStreet] = useState<StreetData | null>(null);
  const [mapInstance, setMapInstance] = useState<any>(null);
  const [streets, setStreets] = useState<StreetData[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const polylineRefs = useRef<{ [key: number]: any }>({});

  useEffect(() => {
    const initialized = mockStreetData.map((street) => {
      const length = calculateStreetLength(street.coordinates);
      const density = length > 0 ? street.carCount / length : 0;
      const color = getColorForTrafficDensity(street.carCount, length);
      return { ...street, length, density, color };
    });
    setStreets(initialized);
  }, []);

  useEffect(() => {
    if (streets.length === 0 || mapInstance) return;

    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href =
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.css";
    document.head.appendChild(link);

    const script = document.createElement("script");
    script.src =
      "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.js";
    script.async = true;

    script.onload = () => {
      if (!mapRef.current || mapInstance || !window.L) return;

      const map = window.L.map(mapRef.current, {
        zoomControl: true,
        attributionControl: true,
      }).setView([45.7969, 24.1521], 15);

      window.L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 19,
      }).addTo(map);

      streets.forEach((street, idx) => {
        const polyline = window.L.polyline(street.coordinates, {
          color: street.color,
          weight: 7,
          opacity: 0.85,
          smoothFactor: 1,
        }).addTo(map);

        polylineRefs.current[idx] = polyline;

        polyline.on("click", () => {
          setSelectedStreet(street);
          map.fitBounds(polyline.getBounds(), { padding: [50, 50] });
        });

        polyline.on("mouseover", function (this: any) {
          this.setStyle({ weight: 12, opacity: 1 });
          this.bringToFront();
        });

        polyline.on("mouseout", function (this: any) {
          this.setStyle({ weight: 7, opacity: 0.85 });
        });

        const tooltip = `
          <div style="font-family: system-ui; padding: 4px 0;">
            <strong>${street.name}</strong><br/>
            <small>${street.carCount} vehicles • ${(
          street.length! * 1000
        ).toFixed(0)}m</small><br/>
            <strong>${street.density!.toFixed(1)} cars/km</strong>
          </div>
        `;
        polyline.bindTooltip(tooltip, { sticky: true });
      });

      setMapInstance(map);
    };

    document.body.appendChild(script);

    return () => {
      mapInstance?.remove();
      setMapInstance(null);
    };
  }, [streets, mapInstance]);

  const updateTrafficData = () => {
    setLoading(true);
    setTimeout(() => {
      const updated = streets.map((street, idx) => {
        const variation = 0.7 + Math.random() * 0.6;
        const newCount = Math.max(1, Math.floor(street.carCount * variation));
        const density = street.length! > 0 ? newCount / street.length! : 0;
        const color = getColorForTrafficDensity(newCount, street.length!);

        if (polylineRefs.current[idx]) {
          polylineRefs.current[idx].setStyle({ color });
          polylineRefs.current[idx].setTooltipContent(`
            <div style="font-family: system-ui;">
              <strong>${street.name}</strong><br/>
              <small>${newCount} vehicles • ${(street.length! * 1000).toFixed(
            0
          )}m</small><br/>
              <strong>${density.toFixed(1)} cars/km</strong>
            </div>
          `);
        }

        return { ...street, carCount: newCount, density, color };
      });

      setStreets(updated);
      setLoading(false);
    }, 600);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200 z-10">
        <div className="max-w-7xl mx-auto px-4 py-5">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Sibiu Traffic Density Monitor
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Real-time traffic visualization • Updated every refresh
              </p>
            </div>
            <div className="flex items-center gap-3">
              {/* <select
                value={currentHour}
                onChange={(e) => setCurrentHour(parseInt(e.target.value))}
                className="px-4 py-2.5 border border-gray-300 rounded-lg text-sm font-medium focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition"
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>
                    {i.toString().padStart(2, "0")}:00
                  </option>
                ))}
              </select> */}
              {/* <button
                onClick={updateTrafficData}
                disabled={loading}
                className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white font-medium rounded-lg shadow-sm transition flex items-center gap-2"
              >
                {loading ? <>Updating...</> : <>Refresh Data</>}
              </button> */}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex-1 flex flex-col lg:flex-row">
        {/* Map */}
        <div style={{ height: 500 }} className="flex-1 relative bg-gray-900">
          <div ref={mapRef} className="absolute inset-0" />
          <div className="absolute top-4 left-4 z-10 bg-white/95 backdrop-blur-sm rounded-lg shadow-lg p-3 text-xs font-medium text-gray-700">
            Click streets for details
          </div>
        </div>

        {/* Sidebar */}
        <aside
          style={{ height: 500 }}
          className="w-full lg:w-96 bg-white shadow-xl border-l border-gray-200 overflow-y-auto"
        >
          <div className="p-6 space-y-8">
            {/* Legend */}
            <div>
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Traffic Legend
              </h2>
              <div className="space-y-3">
                {[
                  { color: "#44dd44", label: "Light", range: "< 80" },
                  { color: "#88cc44", label: "Moderate", range: "80–150" },
                  { color: "#ffaa44", label: "Medium", range: "150–250" },
                  { color: "#ff4444", label: "Heavy", range: "250–400" },
                  { color: "#cc0000", label: "Very Heavy", range: "400+" },
                ].map((item) => (
                  <div key={item.label} className="flex items-center gap-3">
                    <div
                      className="w-16 h-4 rounded-full shadow-sm"
                      style={{ backgroundColor: item.color }}
                    />
                    <div>
                      <div className="font-medium text-gray-800">
                        {item.label}
                      </div>
                      <div className="text-xs text-gray-500">
                        {item.range} cars/km
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Selected Street */}
            {selectedStreet && (
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-5 shadow-md">
                <h3 className="font-bold text-lg text-gray-900 mb-3">
                  Selected Street
                </h3>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="font-semibold">Name:</span>{" "}
                    {selectedStreet.name}
                  </p>
                  <p>
                    <span className="font-semibold">Vehicles:</span>{" "}
                    {selectedStreet.carCount}
                  </p>
                  <p>
                    <span className="font-semibold">Length:</span>{" "}
                    {(selectedStreet.length! * 1000).toFixed(0)} m
                  </p>
                  <p>
                    <span className="font-semibold">Density:</span>{" "}
                    {selectedStreet.density!.toFixed(1)} cars/km
                  </p>
                </div>
                <div className="mt-4 flex items-center gap-3">
                  <span className="text-sm font-semibold">Status:</span>
                  <span
                    className="px-3 py-1.5 rounded-full text-white text-xs font-bold shadow"
                    style={{ backgroundColor: selectedStreet.color }}
                  >
                    {getTrafficLevel(selectedStreet.density || 0)}
                  </span>
                </div>
              </div>
            )}

            {/* Street List */}
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-4">
                Streets by Density • {currentHour.toString().padStart(2, "0")}
                :00
              </h3>
              <div className="space-y-3">
                {streets
                  .sort((a, b) => (b.density || 0) - (a.density || 0))
                  .map((street, idx) => (
                    <div
                      key={idx}
                      onClick={() => setSelectedStreet(street)}
                      className="group cursor-pointer bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-xl p-4 transition-all duration-200 hover:shadow-md hover:scale-[1.02]"
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-semibold text-gray-900 text-sm group-hover:text-blue-700 transition">
                          {street.name}
                        </h4>
                        <span className="text-xs font-bold text-gray-600 bg-gray-200 px-2 py-1 rounded-full">
                          {(street.density || 0).toFixed(0)} cars/km
                        </span>
                      </div>
                      <p className="text-xs text-gray-600 mb-3">
                        {street.carCount} vehicles •{" "}
                        {(street.length! * 1000).toFixed(0)} m
                      </p>
                      <div
                        className="h-3 rounded-full shadow-sm"
                        style={{ backgroundColor: street.color }}
                      />
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
};

export default SibiuTrafficMap;
