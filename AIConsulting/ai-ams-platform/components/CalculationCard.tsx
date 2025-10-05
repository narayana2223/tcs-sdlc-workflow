"use client";

import { useState } from "react";
import { ChevronDown, Calculator } from "lucide-react";
import { cn } from "@/lib/utils";

interface CalculationCardProps {
  formula: string;
  assumptions: string[];
  result: string;
  className?: string;
}

export function CalculationCard({
  formula,
  assumptions,
  result,
  className,
}: CalculationCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={cn("mt-4 border-t border-gray-200 pt-4", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between text-sm font-medium text-gray-700 transition-colors hover:text-blue-600"
      >
        <span className="flex items-center gap-2">
          <Calculator className="h-4 w-4" />
          🧮 Calculation Details
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {isOpen && (
        <div className="mt-3 space-y-4 rounded-lg bg-blue-50 p-4">
          <div>
            <h4 className="mb-2 text-sm font-semibold text-gray-900">
              Formula:
            </h4>
            <code className="block rounded bg-white p-2 text-sm text-gray-800">
              {formula}
            </code>
          </div>

          <div>
            <h4 className="mb-2 text-sm font-semibold text-gray-900">
              Assumptions:
            </h4>
            <ul className="space-y-1 text-sm text-gray-600">
              {assumptions.map((assumption, index) => (
                <li key={index} className="flex items-start gap-2">
                  <span className="mt-0.5 text-blue-600">•</span>
                  <span>{assumption}</span>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h4 className="mb-2 text-sm font-semibold text-gray-900">
              Result:
            </h4>
            <div className="rounded bg-white p-3 text-base font-semibold text-blue-600">
              {result}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
