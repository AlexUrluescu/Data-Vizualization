"use client";
import { Button } from "../ui/button";
import { mockData } from "@/app/mock";
import { Input } from "../ui/input";
import { useState } from "react";

enum CityType {
  ALL_CITIES = "All",
  BIG_CITIES = "Orașe mari",
  MEDIUM_CITIES = "Orașe medii",
  SMALL_CITIES = "Orașe mici",
}

export default function CitiesOptions() {
  const [cityType, setCityType] = useState<CityType>(CityType.ALL_CITIES);
  const [cities, setCities] = useState(mockData);

  const changeCityType = (type: CityType) => {
    setCityType(type);

    if (type === CityType.ALL_CITIES) {
      setCities(mockData);
    } else if (type === CityType.BIG_CITIES) {
      const big_cities = mockData.filter(
        (city) => city.region === CityType.BIG_CITIES
      );
      setCities(big_cities);
    } else if (type === CityType.MEDIUM_CITIES) {
      const medium_cities = mockData.filter(
        (city) => city.region === CityType.MEDIUM_CITIES
      );
      setCities(medium_cities);
    } else {
      const small_cities = mockData.filter(
        (city) => city.region === CityType.SMALL_CITIES
      );
      setCities(small_cities);
    }
  };

  const handleInputSearch = (e: any) => {
    const value = e.target.value;

    const similar_cities = mockData.filter((city) =>
      city.name.toLowerCase().includes(value)
    );

    setCities(similar_cities);
  };

  return (
    <div className="flex flex-col items-center gap-10">
      <Input
        onChange={handleInputSearch}
        className="w-4/5 h-11 bg-white"
        type="email"
        placeholder="City"
      />

      <div style={{ display: "flex", gap: 20 }}>
        <Button
          onClick={() => changeCityType(CityType.ALL_CITIES)}
          style={{
            background: cityType === CityType.ALL_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.ALL_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          All cities
        </Button>
        <Button
          onClick={() => changeCityType(CityType.BIG_CITIES)}
          style={{
            background: cityType === CityType.BIG_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.BIG_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          Orașe mari
        </Button>
        <Button
          onClick={() => changeCityType(CityType.MEDIUM_CITIES)}
          style={{
            background:
              cityType === CityType.MEDIUM_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.MEDIUM_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          Orașe medii
        </Button>
        <Button
          onClick={() => changeCityType(CityType.SMALL_CITIES)}
          style={{
            background:
              cityType === CityType.SMALL_CITIES ? "orange" : "#ededed",
            color: cityType === CityType.SMALL_CITIES ? "white" : "black",
            cursor: "pointer",
          }}
        >
          Orașe mici
        </Button>
      </div>

      <div className="flex justify-center gap-4 flex-wrap">
        {cities.length > 0 ? (
          cities.map((city, index) => (
            <Button
              onClick={() => console.log(city)}
              key={index}
              className="min-w-[10%]"
              variant={"outline"}
            >
              {city.name}
            </Button>
          ))
        ) : (
          <div style={{ padding: 50 }}>No available city</div>
        )}
      </div>
    </div>
  );
}
