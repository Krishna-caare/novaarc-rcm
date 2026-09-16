import { Card, CardContent } from './ui/Card';
import { cn, formatCurrency, formatPercent, formatNumber, getStatusBadge } from '../lib/utils';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

// ── MetricCard ───────────────────────────────────────────────────────────────
interface MetricCardProps {
  title:        string;
  value:        string | number;
  change?:      number;
  changeLabel?: string;
  icon:         React.ReactNode;
  iconBg?:      string;
  trend?:       'up' | 'down' | 'neutral';
  accent?:      'blue' | 'green' | 'amber' | 'purple' | 'red' | 'none';
  subtitle?:    string;
}

export function MetricCard({
  title, value, change, changeLabel, icon, iconBg = 'bg-blue-100 text-blue-600',
  trend = 'neutral', accent = 'none', subtitle,
}: MetricCardProps) {
  const trendColor =
    trend === 'up'   ? 'text-forest-600' :
    trend === 'down' ? 'text-crimson-600' : 'text-slate-500';

  const TrendIcon =
    trend === 'up'   ? TrendingUp :
    trend === 'down' ? TrendingDown : Minus;

  return (
    <Card variant="default" accent={accent} className="transition-all duration-200 hover:-translate-y-0.5 hover:shadow-card-hover">
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{title}</p>
            <p className="mt-2 text-2xl font-bold text-slate-900 tracking-tight animate-count-up">
              {value}
            </p>
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-400">{subtitle}</p>
            )}
            {change !== undefined && (
              <div className="mt-2 flex items-center gap-1">
                <TrendIcon className={cn('w-3.5 h-3.5', trendColor)} />
                <span className={cn('text-xs font-semibold', trendColor)}>
                  {change >= 0 ? '+' : ''}{change.toFixed(1)}%
                </span>
                {changeLabel && (
                  <span className="text-xs text-slate-400">{changeLabel}</span>
                )}
              </div>
            )}
          </div>
          <div className={cn(
            'p-3 rounded-xl flex-shrink-0 flex items-center justify-center',
            iconBg,
          )}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

// ── StatusBadge ──────────────────────────────────────────────────────────────
interface StatusBadgeProps {
  status: string;
  count:  number;
  total:  number;
}

export function StatusBadge({ status, count, total }: StatusBadgeProps) {
  const { className, label } = getStatusBadge(status);
  const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : '0';

  return (
    <div className="flex items-center justify-between px-4 py-2.5 hover:bg-slate-50 rounded-lg transition-colors">
      <div className="flex items-center gap-3">
        <span className={className}>{label}</span>
      </div>
      <div className="text-right">
        <p className="font-semibold text-slate-900 text-sm">{formatNumber(count)}</p>
        <p className="text-2xs text-slate-400">{percentage}%</p>
      </div>
    </div>
  );
}

// ── AgingBucket ──────────────────────────────────────────────────────────────
interface AgingBucketProps {
  label:      string;
  value:      number;
  percentage: number;
  color:      string;
}

export function AgingBucket({ label, value, percentage, color }: AgingBucketProps) {
  return (
    <div className="space-y-1.5">
      <div className="flex justify-between text-sm">
        <span className="text-slate-600 font-medium">{label}</span>
        <span className="font-semibold text-slate-900">{formatCurrency(value)}</span>
      </div>
      <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-700 ease-spring"
          style={{ width: `${Math.min(percentage, 100)}%`, backgroundColor: color }}
        />
      </div>
      <p className="text-2xs text-slate-400 text-right">{percentage.toFixed(1)}% of total AR</p>
    </div>
  );
}

// ── PayerPerformanceRow ──────────────────────────────────────────────────────
interface PayerPerformanceRowProps {
  payer: {
    payer_name:       string;
    total_charged:    number | string;
    total_paid:       number | string;
    collection_rate?: number | string | null;
    denial_rate?:     number | string | null;
    avg_days_to_pay?: number | string | null;
  };
}

export function PayerPerformanceRow({ payer }: PayerPerformanceRowProps) {
  const charged = typeof payer.total_charged === 'number' ? payer.total_charged : parseFloat(String(payer.total_charged || 0)) || 0;
  const paid = typeof payer.total_paid === 'number' ? payer.total_paid : parseFloat(String(payer.total_paid || 0)) || 0;
  
  const rawCollection = payer.collection_rate !== undefined && payer.collection_rate !== null
    ? parseFloat(String(payer.collection_rate))
    : (charged > 0 ? (paid / charged) * 100 : 0);
  const collectionRate = isNaN(rawCollection) ? 0 : rawCollection;

  const rawDenial = payer.denial_rate !== undefined && payer.denial_rate !== null
    ? parseFloat(String(payer.denial_rate))
    : 0;
  const denialRate = isNaN(rawDenial) ? 0 : rawDenial;

  const rawDays = payer.avg_days_to_pay !== undefined && payer.avg_days_to_pay !== null
    ? parseFloat(String(payer.avg_days_to_pay))
    : 0;
  const avgDays = isNaN(rawDays) ? 0 : rawDays;

  const collectionVariant =
    collectionRate >= 90 ? 'bg-forest-50 text-forest-700 ring-1 ring-forest-200' :
    collectionRate >= 70 ? 'bg-amber-50  text-amber-700  ring-1 ring-amber-200'  :
                           'bg-crimson-50 text-crimson-700 ring-1 ring-crimson-200';

  const denialVariant =
    denialRate <= 5  ? 'bg-forest-50 text-forest-700 ring-1 ring-forest-200' :
    denialRate <= 15 ? 'bg-amber-50  text-amber-700  ring-1 ring-amber-200'  :
                       'bg-crimson-50 text-crimson-700 ring-1 ring-crimson-200';

  return (
    <tr className="hover:bg-slate-50/80 transition-colors">
      <td className="px-4 py-3 font-semibold text-slate-900">{payer.payer_name}</td>
      <td className="px-4 py-3 text-slate-600 font-mono text-sm">{formatCurrency(charged)}</td>
      <td className="px-4 py-3 text-slate-600 font-mono text-sm">{formatCurrency(paid)}</td>
      <td className="px-4 py-3">
        <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', collectionVariant)}>
          {formatPercent(collectionRate)}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className={cn('inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold', denialVariant)}>
          {formatPercent(denialRate)}
        </span>
      </td>
      <td className="px-4 py-3 text-slate-600 text-sm">{avgDays.toFixed(1)} days</td>
    </tr>
  );
}

// ── DenialCodeRow ────────────────────────────────────────────────────────────
interface DenialCodeRowProps {
  code: {
    denial_code:  string;
    count:        number;
    total_denied: number;
    avg_denied:   number;
  };
}

export function DenialCodeRow({ code }: DenialCodeRowProps) {
  return (
    <tr className="hover:bg-slate-50/80 transition-colors">
      <td className="px-4 py-3">
        <span className="font-mono font-semibold text-primary-700 bg-primary-50 px-2 py-0.5 rounded text-sm">
          {code.denial_code}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className="font-semibold text-slate-900">{formatNumber(code.count)}</span>
      </td>
      <td className="px-4 py-3 font-mono text-sm text-crimson-700 font-semibold">
        {formatCurrency(code.total_denied)}
      </td>
      <td className="px-4 py-3 text-slate-500 text-sm">{formatCurrency(code.avg_denied)}</td>
    </tr>
  );
}