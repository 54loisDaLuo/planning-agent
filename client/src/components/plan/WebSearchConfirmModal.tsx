import React, { useState, useRef } from 'react';
interface WebSearchConfirmModalProps {
  isOpen: boolean;
  onConfirm: (enableWebSearch: boolean) => void;
  onClose: () => void;
}

const WebSearchConfirmModal: React.FC<WebSearchConfirmModalProps> = ({
  isOpen,
  onConfirm,
  onClose,
}) => {
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const modalRef = useRef<HTMLDivElement>(null);

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    if (modalRef.current) {
      const rect = modalRef.current.getBoundingClientRect();
      setPosition({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging || !modalRef.current) return;

    const modal = modalRef.current;
    const newX = e.clientX - position.x;
    const newY = e.clientY - position.y;

    modal.style.left = `${newX}px`;
    modal.style.top = `${newY}px`;
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-900 bg-opacity-20 bg-transparent flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4 relative shadow-xl border border-gray-200">
        <h3 className="text-lg text-center font-semibold text-gray-800 mb-3">
          是否开启【联网搜索】？
        </h3>
        <p className="text-gray-600 text-center mb-6 text-sm">
          开启后将搜索相关网络资料辅助内容重写
        </p>
        <div className="flex gap-1 justify-between">
          <button
            className="px-6 py-3 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors font-medium text-base mr-auto"
            onClick={() => {
              onConfirm(true);
            }}
          >
            是
          </button>
          <button
            className="px-6 py-3 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors font-medium text-base ml-auto"
            onClick={() => {
              onConfirm(false);
            }}
          >
            否
          </button>
        </div>
        <button
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 text-xl transition-colors"
          onClick={onClose}
        >
          ×
        </button>
      </div>
    </div>
  );
};
export default WebSearchConfirmModal;
