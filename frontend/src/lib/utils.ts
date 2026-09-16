import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(amount: number | string | null | undefined): string {
  if (amount === null || amount === undefined) return '$0.00';
  const num = typeof amount === 'number' ? amount : parseFloat(String(amount));
  if (isNaN(num)) return '$0.00';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(num);
}

export function formatNumber(num: number | string | null | undefined): string {
  if (num === null || num === undefined) return '0';
  const val = typeof num === 'number' ? num : parseFloat(String(num));
  if (isNaN(val)) return '0';
  return new Intl.NumberFormat('en-US').format(val);
}

export function formatPercent(value: number | string | null | undefined): string {
  if (value === null || value === undefined) return '0.0%';
  const num = typeof value === 'number' ? value : parseFloat(String(value));
  if (isNaN(num)) return '0.0%';
  return `${num.toFixed(1)}%`;
}

export function formatDate(dateStr: string | null | undefined): string {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

export function formatDateTime(dateStr: string | null | undefined): string {
  if (!dateStr) return 'N/A';
  return new Date(dateStr).toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function getStatusBadge(status: string): { className: string; label: string } {
  const statusMap: Record<string, { className: string; label: string }> = {
    created: { className: 'badge-neutral', label: 'Created' },
    submitted: { className: 'badge-info', label: 'Submitted' },
    acknowledged: { className: 'badge-info', label: 'Acknowledged' },
    in_process: { className: 'badge-warning', label: 'In Process' },
    paid: { className: 'badge-success', label: 'Paid' },
    denied: { className: 'badge-danger', label: 'Denied' },
    appealed: { className: 'badge-warning', label: 'Appealed' },
    not_started: { className: 'badge-neutral', label: 'Not Started' },
    drafted: { className: 'badge-info', label: 'Drafted' },
    won: { className: 'badge-success', label: 'Won' },
    lost: { className: 'badge-danger', label: 'Lost' },
  };
  return statusMap[status] || { className: 'badge-neutral', label: status };
}

export function getPriorityBadge(priority: string): { className: string; label: string } {
  const priorityMap: Record<string, { className: string; label: string }> = {
    critical: { className: 'badge-danger', label: 'Critical' },
    high: { className: 'badge-danger', label: 'High' },
    medium: { className: 'badge-warning', label: 'Medium' },
    low: { className: 'badge-info', label: 'Low' },
  };
  return priorityMap[priority] || { className: 'badge-neutral', label: priority };
}

export function truncate(str: string, length: number): string {
  if (str.length <= length) return str;
  return str.slice(0, length) + '...';
}