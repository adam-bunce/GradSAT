import React, { useCallback, useRef, useState } from "react";

const MouseSelection = ({ dotw }) => {
  const TOTAL_CHUNKS = 20;
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState(null);
  const [selectionEnd, setSelectionEnd] = useState(null);
  const containerRef = useRef(null);

  const getChunkFromMousePosition = useCallback((mouseY) => {
    const rect = containerRef.current.getBoundingClientRect();
    const containerHeight = rect.height;
    const chunkHeight = containerHeight / TOTAL_CHUNKS;
    const relativeY = mouseY - rect.top;
    const chunk = Math.floor(relativeY / chunkHeight);
    return Math.min(Math.max(chunk, 0), TOTAL_CHUNKS - 1);
  }, []);

  const handleMouseDown = useCallback(
    (e) => {
      const chunk = getChunkFromMousePosition(e.clientY);
      setIsSelecting(true);
      setSelectionStart(chunk);
      setSelectionEnd(chunk);
    },
    [getChunkFromMousePosition],
  );

  const handleMouseMove = useCallback(
    (e) => {
      if (!isSelecting) return;
      const chunk = getChunkFromMousePosition(e.clientY);
      setSelectionEnd(chunk);
    },
    [isSelecting, getChunkFromMousePosition],
  );

  const handleMouseUp = useCallback(() => {
    setIsSelecting(false);
  }, []);

  const getSelectionStyle = () => {
    if (selectionStart === null || selectionEnd === null) return {};

    const startChunk = Math.min(selectionStart, selectionEnd);
    const endChunk = Math.max(selectionStart, selectionEnd);
    const chunkHeight =
      containerRef.current.getBoundingClientRect().height / TOTAL_CHUNKS;

    return {
      position: "absolute",
      top: `${startChunk * chunkHeight}px`,
      height: `${(endChunk - startChunk + 1) * chunkHeight}px`,
      left: 0,
      right: 0,
      backgroundColor: "rgba(59, 130, 246, 0.5)", // blue-500 with opacity
      borderRadius: "6px",
    };
  };

  return (
    <div className="w-full max-w-lg mx-auto p-4">
      <div
        ref={containerRef}
        className="relative h-96 border border-gray-300 rounded cursor-pointer"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
      >
        {selectionStart !== null && selectionEnd !== null && (
          <div style={getSelectionStyle()}>
            {dotw}: {Math.min(selectionStart, selectionEnd)} to{" "}
            {Math.max(selectionStart, selectionEnd)}
          </div>
        )}
      </div>
    </div>
  );
};

export default MouseSelection;
