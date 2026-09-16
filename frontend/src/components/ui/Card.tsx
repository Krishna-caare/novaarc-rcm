import React from 'react';
import { cn } from '../../lib/utils';

interface CardProps {
  className?: string;
  children:   React.ReactNode;
  /** 'default' | 'hover' (adds lift on hover) | 'elevated' | 'flat' */
  variant?:   'default' | 'hover' | 'elevated' | 'flat';
  /** Left accent stripe color (for metric cards) */
  accent?:    'blue' | 'green' | 'amber' | 'purple' | 'red' | 'none';
}

const variantMap: Record<NonNullable<CardProps['variant']>, string> = {
  default:  'bg-white rounded-xl shadow-card border border-slate-200 overflow-hidden',
  hover:    'card-hover',
  elevated: 'card-elevated',
  flat:     'bg-white rounded-xl border border-slate-200 overflow-hidden',
};

const accentMap: Record<NonNullable<Exclude<CardProps['accent'], 'none'>>, string> = {
  blue:   'metric-accent-blue',
  green:  'metric-accent-green',
  amber:  'metric-accent-amber',
  purple: 'metric-accent-purple',
  red:    'metric-accent-red',
};

export function Card({ className, children, variant = 'default', accent = 'none' }: CardProps) {
  return (
    <div
      className={cn(
        variantMap[variant],
        accent !== 'none' && accentMap[accent as keyof typeof accentMap],
        className,
      )}
    >
      {children}
    </div>
  );
}

interface CardHeaderProps {
  className?: string;
  children:   React.ReactNode;
  action?:    React.ReactNode;
}

export function CardHeader({ className, children, action }: CardHeaderProps) {
  return (
    <div className={cn('px-6 py-4 border-b border-slate-200 flex items-center justify-between', className)}>
      <div className="flex-1 min-w-0">{children}</div>
      {action && <div className="ml-4 flex-shrink-0">{action}</div>}
    </div>
  );
}

interface CardTitleProps {
  className?: string;
  children:   React.ReactNode;
  subtitle?:  string;
}

export function CardTitle({ className, children, subtitle }: CardTitleProps) {
  return (
    <div>
      <h3 className={cn('text-base font-semibold text-slate-900 leading-snug', className)}>
        {children}
      </h3>
      {subtitle && <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>}
    </div>
  );
}

interface CardContentProps {
  className?: string;
  children:   React.ReactNode;
}

export function CardContent({ className, children }: CardContentProps) {
  return <div className={cn('p-6', className)}>{children}</div>;
}

interface CardFooterProps {
  className?: string;
  children:   React.ReactNode;
}

export function CardFooter({ className, children }: CardFooterProps) {
  return (
    <div className={cn('px-6 py-4 border-t border-slate-200 bg-slate-50/60 flex items-center justify-between', className)}>
      {children}
    </div>
  );
}