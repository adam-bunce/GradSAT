import { useState } from "react";

const TextSelect = ({ onChange, selectedItems, itemOptions, boxText }) => {
  const [itemInput, setCourseInput] = useState<string>("");
  const [itemSuggestions, setSuggestions] = useState([]);
  const [selectedIndex, setSelectedIndex] = useState(0);

  const filterSuggestions = (value) => {
    if (!value) return [];
    const filtered = itemOptions.filter((option) =>
      option.toLowerCase().includes(value.toLowerCase()),
    );
    return filtered.slice(0, 5);
  };

  const handleInputChange = (e) => {
    const value = e.target.value;
    setCourseInput(value);
    const filtered = filterSuggestions(value);
    setSuggestions(filtered);
    setSelectedIndex(0);
  };

  const handleKeyDown = (e) => {
    switch (e.key) {
      case "ArrowUp":
        e.preventDefault();
        setSelectedIndex((prev) =>
          prev > 0 ? prev - 1 : itemSuggestions.length - 1,
        );
        break;
      case "ArrowDown":
      case "Tab":
        e.preventDefault();
        if (e.shiftKey) {
          setSelectedIndex((prev) =>
            prev > 0 ? prev - 1 : itemSuggestions.length - 1,
          );
        } else {
          setSelectedIndex((prev) =>
            prev < itemSuggestions.length - 1 ? prev + 1 : 0,
          );
        }
        break;
      case "Enter":
      case " ":
        e.preventDefault();
        if (
          itemSuggestions.length &&
          !selectedItems.includes(itemSuggestions[selectedIndex])
        ) {
          onChange([...selectedItems, itemSuggestions[selectedIndex]]);
          setCourseInput("");
          setSuggestions([]);
        }
        break;
    }
  };

  const handleSuggestionClick = (suggestion) => {
    if (!selectedItems.includes(suggestion)) {
      onChange([...selectedItems, suggestion]);
      setCourseInput("");
      setSuggestions([]);
    }
  };

  return (
    <div>
      {selectedItems.map((course, index) => (
        <div className={""}>
          <span
            key={index}
            className="bg-blue-100 text-blue-800 px-2 py-1 text-sm hover:cursor-pointer hover:bg-red-100 hover:text-red-800 "
            onClick={() =>
              onChange(selectedItems.filter((crs) => course !== crs))
            }
          >
            X {course}
          </span>
        </div>
      ))}

      <div className="border  p-2 bg-white">
        <div className="flex flex-wrap gap-2">
          <input
            type="text"
            value={itemInput}
            onChange={handleInputChange}
            onKeyDown={handleKeyDown}
            className="outline-none flex-grow min-w-[100px]"
            placeholder={boxText}
          />
        </div>

        {itemSuggestions.length > 0 && (
          <ul className="mt-1 border-t pt-1">
            {itemSuggestions.map((suggestion, index) => (
              <li
                key={index}
                className={`px-2 py-1 cursor-pointer ${
                  index === selectedIndex ? "bg-blue-50" : ""
                }`}
                onClick={() => handleSuggestionClick(suggestion)}
              >
                {suggestion}
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default TextSelect;
