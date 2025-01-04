"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

export default function ScrollSelect({ zones, labels }) {
  const [selectionStart, setSelectionStart] = useState<number>(null);
  const [selectionEnd, setSelectionEnd] = useState<number>(null);
  const [isSelecting, setIsSelecting] = useState<boolean>(false);
  const [height, setHeight] = useState(0);
  const containerRef = useRef(null);

  useEffect(() => {
    if (containerRef.current) {
      setHeight(containerRef.current.getBoundingClientRect().height);
    }
  }, [containerRef.current]);

  const calculateChunk = useCallback((yPos: number) => {
    const rect = containerRef.current.getBoundingClientRect();
    const zoneHeight: number = Math.floor(rect.height / zones);
    const chunk: number = Math.floor((yPos - rect.top) / zoneHeight);
    return Math.min(Math.max(chunk, 0), zones - 1);
  }, []);

  const handleMouseDown = useCallback((event: React.MouseEvent) => {
    setIsSelecting(true);
    const yPos = calculateChunk(event.clientY);
    setSelectionStart(yPos);
    setSelectionEnd(yPos);
  }, []);

  const handleMouseMove = useCallback(
    (event: React.MouseEvent) => {
      if (!isSelecting) return;
      const yPos = calculateChunk(event.clientY);
      setSelectionEnd(yPos);
    },
    [isSelecting],
  );

  const handleMouseUp = useCallback((event: React.MouseEvent) => {
    setIsSelecting(false);
  }, []);

  const chunksClass = () => {
    if (containerRef.current == null) {
      console.log("cr empty");
      return;
    }

    const rect = containerRef.current.getBoundingClientRect();
    const chunkHeight: number = Math.floor(rect.height / zones);

    return {
      background: `repeating-linear-gradient(
  to bottom,
  transparent 0,
  transparent ${chunkHeight * 4 - 1}px,
  black ${chunkHeight * 4}px,
  black ${chunkHeight * 4 - 1}px
                  )`,
    };
  };

  const boxClass = () => {
    if (selectionEnd == null || selectionStart == null) return;
    const rect = containerRef.current.getBoundingClientRect();
    const chunkHeight: number = Math.floor(rect.height / zones);
    const firstChunk = Math.min(selectionEnd, selectionStart);
    const secondChunk = Math.max(selectionEnd, selectionStart);
    return {
      position: "absolute",
      top: firstChunk * chunkHeight + "px",
      height: (secondChunk - firstChunk + 1) * chunkHeight + "px",
      left: 0,
      right: 0,
    };
  };
  return (
    <>
      <div
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        ref={containerRef}
        style={chunksClass()}
        className={`relative cursor-pointer border-2 border-gray-600 h-full ${isSelecting ? "!cursor-move" : ""}`}
      >
        {selectionStart !== null && selectionEnd !== null && (
          <div
            className={
              "text-white bg-red-500 text-xs pl-2 select-none box-border rounded-lg opacity-85"
            }
            style={boxClass()}
            id={"selection-area"}
            onMouseDown={(e) => {
              if (isSelecting) return;
              e.stopPropagation();
              alert(
                `adjust timestamps ${labels[Math.min(selectionStart, selectionEnd)]} -${labels[Math.max(selectionStart, selectionEnd)]} `,
              );
            }}
          >
            {labels[Math.min(selectionStart, selectionEnd)]} {" - "}
            {labels[Math.max(selectionStart, selectionEnd + 1)]}
          </div>
        )}
      </div>
    </>
  );
}
