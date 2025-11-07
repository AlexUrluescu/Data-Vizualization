"use client";
import React, { useEffect, useRef, useState } from "react";

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
      [45.79178, 24.14986], // capăt sudic (Centrul Civic)
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
      [45.7936, 24.14461], // capăt sudic – aproape de Strada Mitropoliei
      [45.79419, 24.14503], // mijlocul străzii, lângă zidul cetății
      [45.79482, 24.14541],
      [45.79512, 24.14569],
      [45.79536, 24.146], //
    ],
    carCount: 1000,
    color: "#88cc44",
  },
  {
    name: "Strada Emil Cioran",
    coordinates: [
      [45.78957, 24.14665], // capăt sudic – lângă intersecția cu Bulevardul Corneliu Coposu
      [45.7899, 24.14695],
      [45.79018, 24.14714], // centru aproximativ
      [45.79061, 24.14779],
    ],
    carCount: 5,
    color: "#44dd44",
  },
  {
    name: "Strada Mitropoliei",
    coordinates: [
      [45.7935, 24.14614], // capăt sudic (Centrul Civic / Orașul de Jos)
      [45.79433, 24.14688],
      [45.79559, 24.1487],
      [45.79697, 24.15007],
    ],
    carCount: 34,
    color: "#ff8844",
  },
];

// Calculate street length using Haversine formula
const calculateStreetLength = (coordinates: [number, number][]): number => {
  let totalLength = 0;
  for (let i = 0; i < coordinates.length - 1; i++) {
    const [lat1, lon1] = coordinates[i];
    const [lat2, lon2] = coordinates[i + 1];

    const R = 6371; // Earth's radius in km
    const dLat = ((lat2 - lat1) * Math.PI) / 180;
    const dLon = ((lon2 - lon1) * Math.PI) / 180;
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos((lat1 * Math.PI) / 180) *
        Math.cos((lat2 * Math.PI) / 180) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    totalLength += R * c;
  }
  return totalLength;
};

// Get color based on traffic density (vehicles per km)
const getColorForTrafficDensity = (
  carCount: number,
  streetLength: number
): string => {
  if (streetLength === 0) return "#888888";

  // Calculate density: vehicles per kilometer
  const density = carCount / streetLength;

  // Density thresholds (vehicles/km)
  // These can be adjusted based on your traffic analysis
  if (density >= 400) return "#cc0000"; // Very Heavy: 400+ cars/km
  if (density >= 250) return "#ff4444"; // Heavy: 250-400 cars/km
  if (density >= 150) return "#ffaa44"; // Medium: 150-250 cars/km
  if (density >= 80) return "#88cc44"; // Moderate: 80-150 cars/km
  return "#44dd44"; // Light: <80 cars/km
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

  // Initialize streets with calculated lengths and densities
  useEffect(() => {
    const initializedStreets = mockStreetData.map((street) => {
      const length = calculateStreetLength(street.coordinates);
      const density = length > 0 ? street.carCount / length : 0;
      const color = getColorForTrafficDensity(street.carCount, length);

      return {
        ...street,
        length,
        density,
        color,
      };
    });

    setStreets(initializedStreets);
  }, []);

  useEffect(() => {
    if (streets.length === 0) return;

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
      if (mapRef.current && !mapInstance && window.L) {
        const map = window.L.map(mapRef.current).setView(
          [45.7969, 24.1521],
          14
        );

        window.L.tileLayer(
          "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
          {
            attribution: "© OpenStreetMap contributors",
          }
        ).addTo(map);

        streets.forEach((street: StreetData, idx: number) => {
          const polyline = window.L.polyline(street.coordinates, {
            color: street.color,
            weight: 6,
            opacity: 0.8,
          }).addTo(map);

          polylineRefs.current[idx] = polyline;

          polyline.on("click", () => {
            setSelectedStreet(street);
          });

          polyline.on("mouseover", function (this: any) {
            this.setStyle({ weight: 10, opacity: 1 });
          });

          polyline.on("mouseout", function (this: any) {
            this.setStyle({ weight: 6, opacity: 0.8 });
          });

          const tooltipContent = `
            <strong>${street.name}</strong><br/>
            Cars: ${street.carCount}<br/>
            Length: ${(street.length! * 1000).toFixed(0)}m<br/>
            Density: ${street.density!.toFixed(1)} cars/km
          `;

          polyline.bindTooltip(tooltipContent, {
            permanent: false,
            direction: "top",
          });
        });

        setMapInstance(map);
      }
    };

    document.body.appendChild(script);

    return () => {
      if (mapInstance) {
        mapInstance.remove();
      }
    };
  }, [streets]);

  const updateTrafficData = (): void => {
    const variation = Math.random() * 0.4 + 0.8;

    const updatedStreets = streets.map((street, idx) => {
      const newCount = Math.floor(street.carCount * variation);
      const density = street.length! > 0 ? newCount / street.length! : 0;
      const newColor = getColorForTrafficDensity(newCount, street.length!);

      const updated = {
        ...street,
        carCount: newCount,
        density,
        color: newColor,
      };

      if (polylineRefs.current[idx]) {
        polylineRefs.current[idx].setStyle({ color: newColor });
        const tooltipContent = `
          <strong>${street.name}</strong><br/>
          Cars: ${newCount}<br/>
          Length: ${(street.length! * 1000).toFixed(0)}m<br/>
          Density: ${density.toFixed(1)} cars/km
        `;
        polylineRefs.current[idx].setTooltipContent(tooltipContent);
      }

      return updated;
    });

    setStreets(updatedStreets);

    if (selectedStreet) {
      const updated = updatedStreets.find(
        (s: StreetData) => s.name === selectedStreet.name
      );
      if (updated) {
        setSelectedStreet(updated);
      }
    }
  };

  const handleHourChange = (e: React.ChangeEvent<HTMLSelectElement>): void => {
    const newHour = parseInt(e.target.value);
    setCurrentHour(newHour);
  };

  return (
    <div style={{ height: 500 }} className="w-full bg-gray-100 flex flex-col">
      <div className="bg-white shadow-md p-4">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-2xl font-bold text-gray-800 mb-2">
            Sibiu Traffic Density Monitor
          </h1>
          <p className="text-sm text-gray-600 mb-3">
            Color based on traffic density (vehicles per kilometer)
          </p>
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700">
                Current Hour:
              </label>
              <select
                value={currentHour}
                onChange={handleHourChange}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm"
              >
                {Array.from({ length: 24 }, (_, i) => (
                  <option key={i} value={i}>
                    {i.toString().padStart(2, "0")}:00
                  </option>
                ))}
              </select>
            </div>
            <button
              onClick={updateTrafficData}
              disabled={loading}
              className="px-4 py-1 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 transition disabled:opacity-50"
            >
              {loading ? "Loading..." : "Refresh Data"}
            </button>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        <div className="flex-1 relative">
          <div ref={mapRef} className="w-full h-full" />
        </div>

        <div className="w-80 bg-white shadow-lg p-4 overflow-y-auto">
          <h2 className="text-lg font-bold text-gray-800 mb-4">
            Traffic Density Legend
          </h2>

          <div className="space-y-2 mb-6">
            <div className="flex items-center gap-2">
              <div
                className="w-12 h-3 rounded"
                style={{ backgroundColor: "#44dd44" }}
              />
              <span className="text-sm text-gray-700">
                &lt;80 cars/km (Light)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-12 h-3 rounded"
                style={{ backgroundColor: "#88cc44" }}
              />
              <span className="text-sm text-gray-700">
                80-150 cars/km (Moderate)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-12 h-3 rounded"
                style={{ backgroundColor: "#ffaa44" }}
              />
              <span className="text-sm text-gray-700">
                150-250 cars/km (Medium)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-12 h-3 rounded"
                style={{ backgroundColor: "#ff4444" }}
              />
              <span className="text-sm text-gray-700">
                250-400 cars/km (Heavy)
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div
                className="w-12 h-3 rounded"
                style={{ backgroundColor: "#cc0000" }}
              />
              <span className="text-sm text-gray-700">
                400+ cars/km (Very Heavy)
              </span>
            </div>
          </div>

          {selectedStreet && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <h3 className="font-bold text-gray-800 mb-2">Selected Street</h3>
              <p className="text-sm text-gray-700 mb-1">
                <strong>Name:</strong> {selectedStreet.name}
              </p>
              <p className="text-sm text-gray-700 mb-1">
                <strong>Cars:</strong> {selectedStreet.carCount}
              </p>
              <p className="text-sm text-gray-700 mb-1">
                <strong>Length:</strong>{" "}
                {((selectedStreet.length || 0) * 1000).toFixed(0)}m
              </p>
              <p className="text-sm text-gray-700 mb-1">
                <strong>Density:</strong>{" "}
                {(selectedStreet.density || 0).toFixed(1)} cars/km
              </p>
              <div className="flex items-center gap-2 mt-2">
                <strong className="text-sm">Status:</strong>
                <div
                  className="px-2 py-1 rounded text-xs font-medium text-white"
                  style={{ backgroundColor: selectedStreet.color }}
                >
                  {getTrafficLevel(selectedStreet.density || 0)}
                </div>
              </div>
            </div>
          )}

          <h3 className="text-md font-bold text-gray-800 mb-3">
            All Streets (by Density) - {currentHour.toString().padStart(2, "0")}
            :00
          </h3>
          <div className="space-y-2">
            {streets
              .sort((a, b) => (b.density || 0) - (a.density || 0))
              .map((street, idx) => (
                <div
                  key={idx}
                  onClick={() => setSelectedStreet(street)}
                  className="p-3 bg-gray-50 rounded-lg border border-gray-200 hover:bg-gray-100 cursor-pointer transition"
                >
                  <div className="flex justify-between items-start mb-1">
                    <span className="text-sm font-medium text-gray-800">
                      {street.name}
                    </span>
                    <span className="text-xs font-bold text-gray-700">
                      {(street.density || 0).toFixed(1)} cars/km
                    </span>
                  </div>
                  <div className="text-xs text-gray-600 mb-2">
                    {street.carCount} cars •{" "}
                    {((street.length || 0) * 1000).toFixed(0)}m
                  </div>
                  <div
                    className="w-full h-2 rounded"
                    style={{ backgroundColor: street.color }}
                  />
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SibiuTrafficMap;
