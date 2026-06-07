// @ts-nocheck
import React from 'react';

type Toast = {
  id: number;
  message: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  durationMs?: number;
};

type ToastContextValue = {
  show: (message: string, opts?: { type?: Toast['type']; durationMs?: number }) => void;
};

const ToastContext = React.createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error('useToast must be used within <ToastProvider>');
  return ctx;
}

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = React.useState<Toast[]>([]);
  const idRef = React.useRef(1);

  const remove = React.useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = React.useCallback((message: string, opts?: { type?: Toast['type']; durationMs?: number }) => {
    const id = idRef.current++;
    const toast: Toast = { id, message, type: opts?.type ?? 'success', durationMs: opts?.durationMs ?? 2500 };
    setToasts((prev) => [...prev, toast]);
    window.setTimeout(() => remove(id), toast.durationMs);
  }, [remove]);

  return (
    <ToastContext.Provider value={{ show }}>
      {children}
      <div aria-live="polite" aria-atomic="true" style={{ position: 'fixed', right: 16, bottom: 16, display: 'grid', gap: 8, zIndex: 1000 }}>
        {toasts.map((t) => (
          <div key={t.id} role="status" style={{
            minWidth: 200,
            maxWidth: 360,
            padding: '10px 12px',
            borderRadius: 8,
            boxShadow: '0 6px 18px rgba(0,0,0,0.18)',
            background: t.type === 'success' ? '#059669' : t.type === 'error' ? '#dc2626' : t.type === 'warning' ? '#d97706' : '#2563eb',
            color: 'white',
          }}>
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// Global toast (no provider required). Creates a lightweight DOM container and message elements.
let toastContainer: HTMLDivElement | null = null;

function ensureToastContainer() {
  if (toastContainer && document.body.contains(toastContainer)) return toastContainer;
  toastContainer = document.createElement('div');
  toastContainer.setAttribute('aria-live', 'polite');
  toastContainer.setAttribute('aria-atomic', 'true');
  Object.assign(toastContainer.style, {
    position: 'fixed',
    right: '16px',
    bottom: '16px',
    display: 'grid',
    gap: '8px',
    zIndex: '1000',
  } as CSSStyleDeclaration);
  document.body.appendChild(toastContainer);
  return toastContainer;
}

export function showToast(message: string, opts?: { type?: 'success' | 'error' | 'info' | 'warning'; durationMs?: number }) {
  const container = ensureToastContainer();
  const el = document.createElement('div');
  el.setAttribute('role', 'status');
  const type = opts?.type ?? 'success';
  const bg = type === 'success' ? '#059669' : type === 'error' ? '#dc2626' : type === 'warning' ? '#d97706' : '#2563eb';
  Object.assign(el.style, {
    minWidth: '200px',
    maxWidth: '360px',
    padding: '10px 12px',
    borderRadius: '8px',
    boxShadow: '0 6px 18px rgba(0,0,0,0.18)',
    background: bg,
    color: 'white',
  } as CSSStyleDeclaration);
  el.textContent = message;
  container.appendChild(el);
  const ms = opts?.durationMs ?? 2500;
  window.setTimeout(() => {
    el.remove();
    // Clean up container if empty
    if (toastContainer && toastContainer.childElementCount === 0) {
      toastContainer.remove();
      toastContainer = null;
    }
  }, ms);
}


