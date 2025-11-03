"use client";
import { Button } from "../ui/button";
import { mockData } from "@/app/mock";
import { Input } from "../ui/input";

export default function CitiesOptions() {
  return (
    <div className="flex flex-col items-center gap-10">
      <Input className="w-4/5 h-11 bg-white" type="email" placeholder="Email" />

      <div className="flex justify-center gap-4 flex-wrap">
        {mockData.map((city, index) => (
          <Button
            onClick={() => console.log(city)}
            key={index}
            className="min-w-[10%]"
            variant={"outline"}
          >
            {city.name}
          </Button>
        ))}
      </div>
    </div>
  );
}
