import { useEffect, useRef, useState } from "react";
import "./TextModal.css";

interface TextModalProps {
  title: string;
  initialValue: string;
  onSave: (value: string) => void;
  onClose: () => void;
}

export function TextModal({ title, initialValue, onSave, onClose }: TextModalProps) {
  const [value, setValue] = useState<string>(initialValue);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  return (
    <div className="text-modal__backdrop" role="dialog" aria-modal="true" aria-label={title}>
      <div className="text-modal">
        <header className="text-modal__header">
          <h2>{title}</h2>
          <button type="button" className="text-modal__close" onClick={onClose} aria-label="關閉">
            ×
          </button>
        </header>
        <div className="text-modal__body">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(event) => setValue(event.target.value)}
            spellCheck={false}
            placeholder="請貼上或輸入完整內容"
          />
        </div>
        <footer className="text-modal__footer">
          <button type="button" onClick={() => onSave(value)}>
            儲存
          </button>
        </footer>
      </div>
    </div>
  );
}
