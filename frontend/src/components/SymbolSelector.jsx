import React, { useState, useEffect, useRef } from 'react';
import { CRYPTO_SYMBOLS, STOCK_SYMBOLS } from '../data/symbols';
import { ChevronDown, Search } from 'lucide-react';

const SymbolSelector = ({ assetType, selectedSymbol, onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const wrapperRef = useRef(null);

  // Determine which list to use
  const options = assetType === 'CRYPTO' ? CRYPTO_SYMBOLS : STOCK_SYMBOLS;

  // Filter options based on search term
  const filteredOptions = options.filter(option =>
    option.label.toLowerCase().includes(searchTerm.toLowerCase()) ||
    option.value.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [wrapperRef]);

  // Update search term when selectedSymbol changes externally
  useEffect(() => {
    setSearchTerm('');
  }, [selectedSymbol]);

  const handleSelect = (symbol) => {
    onSelect(symbol);
    setIsOpen(false);
    setSearchTerm('');
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (filteredOptions.length > 0) {
        handleSelect(filteredOptions[0].value);
      } else if (searchTerm) {
        handleSelect(searchTerm.toUpperCase());
      }
    }
  };

  return (
    <div className="relative w-full" ref={wrapperRef}>
      
      {/* Trigger Button / Input */}
      <div 
        className="relative"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center w-full px-3 py-2 bg-white border border-gray-300 rounded-md shadow-sm focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500 cursor-pointer">
            <span className="flex-grow text-gray-900">
                {selectedSymbol || "Select Symbol"}
            </span>
            <ChevronDown className="w-4 h-4 text-gray-500" />
        </div>
      </div>

      {/* Dropdown Menu */}
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-hidden flex flex-col">
          {/* Search Input */}
          <div className="p-2 border-b border-gray-200 bg-gray-50 sticky top-0">
            <div className="relative">
                <Search className="absolute left-2 top-2.5 w-4 h-4 text-gray-400" />
                <input
                    type="text"
                    className="w-full pl-8 pr-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Search symbol..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    onKeyDown={handleKeyDown}
                    autoFocus
                    onClick={(e) => e.stopPropagation()} // Prevent closing when clicking input
                />
            </div>
          </div>

          {/* Options List */}
          <div className="overflow-y-auto flex-grow">
            {filteredOptions.length > 0 ? (
              filteredOptions.map((option) => (
                <div
                  key={option.value}
                  className={`px-4 py-2 text-sm cursor-pointer hover:bg-blue-50 ${
                    selectedSymbol === option.value ? 'bg-blue-100 text-blue-700 font-medium' : 'text-gray-700'
                  }`}
                  onClick={() => handleSelect(option.value)}
                >
                  {option.label}
                </div>
              ))
            ) : (
               // Allow selecting the custom search term if no match found
               searchTerm && (
                   <div 
                        className="px-4 py-2 text-sm cursor-pointer hover:bg-blue-50 text-blue-600 font-medium border-t border-gray-100"
                        onClick={() => handleSelect(searchTerm.toUpperCase())}
                   >
                       Use custom symbol: "{searchTerm.toUpperCase()}"
                   </div>
               ) || (
                  <div className="px-4 py-3 text-sm text-gray-500 text-center">
                    No symbols found
                  </div>
               )
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default SymbolSelector;
