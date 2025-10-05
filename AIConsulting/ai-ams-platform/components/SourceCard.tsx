"use client";

import { useState } from "react";
import { ChevronDown, FileText } from "lucide-react";
import { cn } from "@/lib/utils";

interface Source {
  title: string;
  organization?: string;
  year?: number;
  type?: string;
}

interface SourceCardProps {
  sources: (string | Source)[];
  className?: string;
}

export function SourceCard({ sources, className }: SourceCardProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className={cn("mt-4 border-t border-gray-200 pt-4", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between text-sm font-medium text-gray-700 transition-colors hover:text-blue-600"
      >
        <span className="flex items-center gap-2">
          <FileText className="h-4 w-4" />
          💡 Sources & Data Verification
        </span>
        <ChevronDown
          className={cn(
            "h-4 w-4 transition-transform",
            isOpen && "rotate-180"
          )}
        />
      </button>

      {isOpen && (
        <div className="mt-3 space-y-2 rounded-lg bg-gray-50 p-4">
          <ul className="space-y-2 text-sm text-gray-600">
            {sources.map((source, index) => (
              <li key={index} className="flex items-start gap-2">
                <span className="mt-0.5 text-blue-600">•</span>
                <span>
                  {typeof source === "string" ? source : (
                    <>
                      <span className="font-medium">{source.title}</span>
                      {source.organization && ` - ${source.organization}`}
                      {source.year && ` (${source.year})`}
                    </>
                  )}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
