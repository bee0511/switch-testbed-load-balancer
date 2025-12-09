import { useEffect, useState } from "react";
import "./TokenPrompt.css";

type TokenPromptProps = {
  open: boolean;
  initialToken?: string;
  onSubmit: (token: string) => void;
  onCancel?: () => void;
};

export function TokenPrompt({
  open,
  initialToken = "",
  onSubmit,
  onCancel,
}: TokenPromptProps) {
  const [value, setValue] = useState(initialToken);

  useEffect(() => {
    setValue(initialToken);
  }, [initialToken, open]);

  if (!open) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSubmit(value);
  };

  return (
    <div className="token-overlay">
      <div className="token-card">
        <h2>輸入 API Token</h2>
        <p>需要 Bearer Token 才能載入設備清單。Token 只會保存在此瀏覽器。</p>

        <form onSubmit={handleSubmit} className="token-form">
          <label>
            Bearer Token
            <input
              type="password"
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder="請輸入 API Token"
              autoFocus
            />
          </label>

          <div className="token-actions">
            {onCancel && (
              <button type="button" className="secondary" onClick={onCancel}>
                取消
              </button>
            )}
            <button type="submit" className="primary">
              儲存 Token
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
