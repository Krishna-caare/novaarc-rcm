import React, { useEffect, useRef, useCallback } from 'react';
import { X } from 'lucide-react';
import { cn } from '../../lib/utils';
import { Button } from './Button';

type ModalSize = 'sm' | 'md' | 'lg' | 'xl' | '2xl' | '3xl' | '4xl' | '5xl' | 'full';

interface ModalProps {
  open:       boolean;
  onClose:    () => void;
  title?:     React.ReactNode;
  subtitle?:  string;
  size?:      ModalSize;
  children:   React.ReactNode;
  footer?:    React.ReactNode;
  className?: string;
  /** Prevent clicking outside to close */
  persistent?: boolean;
}

const sizeClasses: Record<ModalSize, string> = {
  sm:    'max-w-sm',
  md:    'max-w-md',
  lg:    'max-w-lg',
  xl:    'max-w-xl',
  '2xl': 'max-w-2xl',
  '3xl': 'max-w-3xl',
  '4xl': 'max-w-4xl',
  '5xl': 'max-w-5xl',
  full:  'max-w-6xl',
};

export function Modal({
  open,
  onClose,
  title,
  subtitle,
  size      = 'md',
  children,
  footer,
  className,
  persistent = false,
}: ModalProps) {
  const contentRef = useRef<HTMLDivElement>(null);
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  const hasFocusedRef = useRef(false);

  // Focus management on modal open
  useEffect(() => {
    if (!open) {
      hasFocusedRef.current = false;
      return;
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !persistent) onCloseRef.current();
    };

    document.addEventListener('keydown', handleKeyDown);
    document.body.style.overflow = 'hidden';

    // Focus only once on initial open, preferring inputs over the close button
    if (!hasFocusedRef.current) {
      hasFocusedRef.current = true;
      setTimeout(() => {
        if (!contentRef.current) return;
        // If an input is already focused, don't steal focus
        if (contentRef.current.contains(document.activeElement) && document.activeElement !== contentRef.current) {
          return;
        }
        const inputElement = contentRef.current.querySelector<HTMLElement>('input:not([type="hidden"]), select, textarea');
        if (inputElement) {
          inputElement.focus();
        } else {
          const focusable = contentRef.current.querySelector<HTMLElement>(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])',
          );
          focusable?.focus();
        }
      }, 50);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [open, persistent]);

  const handleOverlayClick = useCallback((e: React.MouseEvent) => {
    if (!persistent && e.target === e.currentTarget) onCloseRef.current();
  }, [persistent]);

  if (!open) return null;

  return (
    <div
      className="modal-overlay"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? 'modal-title' : undefined}
      onClick={handleOverlayClick}
    >
      <div
        ref={contentRef}
        className={cn('modal-content', sizeClasses[size], 'w-full', className)}
      >
        {/* Header */}
        {(title || subtitle) && (
          <div className="modal-header">
            <div className="flex-1 min-w-0">
              {title && (
                <h2 id="modal-title" className="text-lg font-semibold text-slate-900 leading-snug">
                  {title}
                </h2>
              )}
              {subtitle && (
                <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>
              )}
            </div>
            <button
              type="button"
              tabIndex={-1}
              onClick={onClose}
              className="ml-4 p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100
                         transition-colors flex-shrink-0"
              aria-label="Close modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        )}

        {/* Body */}
        <div className="modal-body scrollbar-thin">
          {children}
        </div>

        {/* Footer */}
        {footer && (
          <div className="modal-footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Convenience wrappers ────────────────────────────────────────────────────
interface ConfirmModalProps {
  open:         boolean;
  onClose:      () => void;
  onConfirm:    () => void;
  title?:       string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?:  string;
  isLoading?:    boolean;
  variant?:      'danger' | 'primary';
}

export function ConfirmModal({
  open,
  onClose,
  onConfirm,
  title       = 'Confirm Action',
  description = 'Are you sure you want to proceed?',
  confirmLabel = 'Confirm',
  cancelLabel  = 'Cancel',
  isLoading    = false,
  variant      = 'danger',
}: ConfirmModalProps) {
  return (
    <Modal
      open={open}
      onClose={onClose}
      title={title}
      size="sm"
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button variant={variant} onClick={onConfirm} isLoading={isLoading}>
            {confirmLabel}
          </Button>
        </>
      }
    >
      <p className="text-slate-600 text-sm leading-relaxed">{description}</p>
    </Modal>
  );
}
