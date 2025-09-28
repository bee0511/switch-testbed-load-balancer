import { useEffect, useRef, useState } from "react";
import "./TextEntryModal.css";

interface TextEntryModalProps {
  open: boolean;
  title: string;
  value: string;
  onSave: (value: string) => void;
  onClose: () => void;
}

export function TextEntryModal({ open, title, value, onSave, onClose }: TextEntryModalProps) {
  const [draft, setDraft] = useState<string>(value);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (open) {
      setDraft(value);
    }
  }, [open, value]);

  useEffect(() => {
    if (open && textareaRef.current) {
      textareaRef.current.focus();
    }
  }, [open]);

  if (!open) {
    return null;
  }

  return (
    <div className="text-modal" role="dialog" aria-modal="true">
      <div className="text-modal__backdrop" onClick={onClose} aria-hidden="true" />
      <div className="text-modal__container">
        <header className="text-modal__header">
          <h2>{title}</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="關閉大量文字輸入">
            ×
          </button>
        </header>
        <div className="text-modal__body">
          <textarea
            ref={textareaRef}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            spellCheck={false}
            placeholder="請在此貼上完整內容"
          />
        </div>
        <footer className="text-modal__footer">
          <button type="button" onClick={() => onSave(draft)}>
            儲存
          </button>
        </footer>
      </div>
    </div>
  );
}
