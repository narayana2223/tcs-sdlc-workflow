'use client';

import { X } from 'lucide-react';
import { useEffect, useRef } from 'react';
import mermaid from 'mermaid';

interface DiagramModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  diagram: string;
  description: string;
  maturityLevel: string;
}

export function DiagramModal({
  isOpen,
  onClose,
  title,
  diagram,
  description,
  maturityLevel
}: DiagramModalProps) {
  const diagramRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (isOpen && diagramRef.current && diagram) {
      // Initialize mermaid
      mermaid.initialize({
        startOnLoad: true,
        theme: 'base',
        themeVariables: {
          primaryColor: '#E94B3C',
          primaryTextColor: '#ffffff',
          primaryBorderColor: '#C23729',
          lineColor: '#333333',
          secondaryColor: '#4A90E2',
          secondaryTextColor: '#ffffff',
          tertiaryColor: '#F5A623',
          tertiaryTextColor: '#000000',
          background: '#FAF9F6',
          mainBkg: '#FAF9F6',
          secondBkg: '#E8F4F8',
          tertiaryBkg: '#FFF4E6',
          nodeBorder: '#333333',
          clusterBkg: '#F5F5F5',
          clusterBorder: '#999999',
          titleColor: '#333333',
          edgeLabelBackground: '#ffffff',
          nodeTextColor: '#333333',
          // Specific node type colors
          actorBkg: '#4A90E2',
          actorBorder: '#2E5C8A',
          actorTextColor: '#ffffff',
          actorLineColor: '#2E5C8A',
          labelBoxBkgColor: '#E8F4F8',
          labelBoxBorderColor: '#4A90E2',
          labelTextColor: '#333333',
          loopTextColor: '#333333',
          noteBorderColor: '#999999',
          noteBkgColor: '#FFF9E6',
          noteTextColor: '#333333',
          // Additional colors for better contrast
          signalColor: '#333333',
          signalTextColor: '#ffffff',
          labelColor: '#333333',
          errorBkgColor: '#ffcccc',
          errorTextColor: '#cc0000',
        },
        flowchart: {
          useMaxWidth: true,
          htmlLabels: true,
          curve: 'basis',
          padding: 20,
          nodeSpacing: 100,
          rankSpacing: 100,
          wrappingWidth: 200,
        },
        fontSize: 14,
      });

      // Render diagram
      const renderDiagram = async () => {
        try {
          const { svg } = await mermaid.render(`mermaid-${Date.now()}`, diagram);
          if (diagramRef.current) {
            diagramRef.current.innerHTML = svg;

            // Apply additional CSS for better text visibility
            const svgElement = diagramRef.current.querySelector('svg');
            if (svgElement) {
              const style = document.createElement('style');
              style.textContent = `
                .node rect, .node circle, .node ellipse, .node polygon, .node path {
                  stroke: #333 !important;
                  stroke-width: 2px !important;
                }
                .node .label, .nodeLabel, .cluster-label {
                  color: #333 !important;
                  fill: #333 !important;
                  font-weight: 600 !important;
                  font-size: 14px !important;
                }
                .edgeLabel {
                  background-color: rgba(250, 249, 246, 0.85) !important;
                  color: #333 !important;
                  fill: #333 !important;
                  font-weight: 600 !important;
                  font-size: 13px !important;
                  padding: 2px 6px !important;
                  border-radius: 3px !important;
                  white-space: nowrap !important;
                  overflow: visible !important;
                }
                .edgeLabel rect {
                  fill: rgba(250, 249, 246, 0.85) !important;
                  stroke: none !important;
                  rx: 3px !important;
                }
                .edgeLabel span {
                  color: #333 !important;
                  font-weight: 600 !important;
                  white-space: nowrap !important;
                }
                .label foreignObject {
                  color: #333 !important;
                  overflow: visible !important;
                }
                .label foreignObject div {
                  color: #333 !important;
                  white-space: nowrap !important;
                }
                text {
                  fill: #333 !important;
                  font-weight: 600 !important;
                  font-size: 14px !important;
                }
                text.edgeLabel {
                  font-size: 13px !important;
                }
                /* Ensure styled nodes have proper text color */
                [style*="fill:#E94B3C"] ~ text,
                [style*="fill:#4A90E2"] ~ text,
                [style*="fill:#F5A623"] ~ text {
                  fill: #ffffff !important;
                }
              `;
              svgElement.appendChild(style);
            }
          }
        } catch (error) {
          console.error('Mermaid render error:', error);
          if (diagramRef.current) {
            diagramRef.current.innerHTML = '<p class="text-red-600">Error rendering diagram</p>';
          }
        }
      };

      renderDiagram();
    }
  }, [isOpen, diagram]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={onClose}
    >
      <div
        className="relative max-h-[90vh] w-full max-w-5xl overflow-y-auto rounded-xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-center justify-between border-b-2 border-gray-200 bg-gradient-to-r from-gray-50 to-white px-6 py-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
            <p className="mt-1 text-sm text-gray-600">
              <span className="font-semibold text-[#E94B3C]">{maturityLevel}</span> - {description}
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 transition-colors hover:bg-gray-100"
            aria-label="Close modal"
          >
            <X size={24} className="text-gray-600" />
          </button>
        </div>

        {/* Diagram Content */}
        <div className="p-6">
          <div
            ref={diagramRef}
            className="flex justify-center overflow-x-auto rounded-lg bg-[#FAF9F6] p-6"
          />
        </div>

        {/* Footer */}
        <div className="border-t border-gray-200 bg-gray-50 px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Click on components in the main workflow to see detailed diagrams
            </div>
            <button
              onClick={onClose}
              className="rounded-lg bg-[#E94B3C] px-6 py-2 font-semibold text-white transition-colors hover:bg-[#C23729]"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
