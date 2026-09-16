import React from 'react';
import { cn } from '../../lib/utils';

type BadgeVariant =
  | 'success' | 'warning' | 'danger' | 'info' | 'neutral' | 'primary' | 'purple';

interface BadgeProps {
  variant?:  BadgeVariant;
  dot?:      boolean;
  size?:     'sm' | 'md';
  children:  React.ReactNode;
  className?: string;
}

const variantClasses: Record<BadgeVariant, string> = {
  success: 'badge-success',
  warning: 'badge-warning',
  danger:  'badge-danger',
  info:    'badge-info',
  neutral: 'badge-neutral',
  primary: 'badge-primary',
  purple:  'badge-purple',
};

const dotColors: Record<BadgeVariant, string> = {
  success: 'bg-forest-500',
  warning: 'bg-amber-500',
  danger:  'bg-crimson-500',
  info:    'bg-blue-500',
  neutral: 'bg-slate-400',
  primary: 'bg-primary-600',
  purple:  'bg-purple-500',
};

export function Badge({ variant = 'neutral', dot = false, size = 'md', children, className }: BadgeProps) {
  return (
    <span
      className={cn(
        variantClasses[variant],
        size === 'sm' && 'text-2xs px-2 py-0.5',
        className,
      )}
    >
      {dot && (
        <span className={cn('block w-1.5 h-1.5 rounded-full flex-shrink-0', dotColors[variant])} />
      )}
      {children}
    </span>
  );
}

// ── Claim Status Badge ──────────────────────────────────────────────────────
const STATUS_CONFIGS: Record<string, { variant: BadgeVariant; label: string }> = {
  created:      { variant: 'neutral',  label: 'Created'      },
  submitted:    { variant: 'info',     label: 'Submitted'    },
  acknowledged: { variant: 'primary',  label: 'Acknowledged' },
  in_process:   { variant: 'warning',  label: 'In Process'   },
  paid:         { variant: 'success',  label: 'Paid'         },
  denied:       { variant: 'danger',   label: 'Denied'       },
  appealed:     { variant: 'purple',   label: 'Appealed'     },
  approved:     { variant: 'success',  label: 'Approved'     },
  rejected:     { variant: 'danger',   label: 'Rejected'     },
  edited:       { variant: 'warning',  label: 'Edited'       },
};

interface ClaimStatusBadgeProps {
  status: string;
  dot?:   boolean;
  size?:  'sm' | 'md';
}

export function ClaimStatusBadge({ status, dot = true, size = 'md' }: ClaimStatusBadgeProps) {
  const config = STATUS_CONFIGS[status.toLowerCase()] ?? {
    variant: 'neutral' as BadgeVariant,
    label: status.charAt(0).toUpperCase() + status.slice(1).replace(/_/g, ' '),
  };
  return (
    <Badge variant={config.variant} dot={dot} size={size}>
      {config.label}
    </Badge>
  );
}
