import { Card, CardContent } from './ui/Card';
import { cn, formatCurrency, formatPercent, formatNumber, getStatusBadge } from '../lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  changeLabel?: string;
  icon: React.ReactNode;
  iconColor: string;
  trend?: 'up' | 'down' | 'neutral';
}

export function MetricCard({ title, value, change, changeLabel, icon, iconColor, trend = 'neutral' }: MetricCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm font-medium text-slate-600">{title}</p>
            <p className="mt-2 text-3xl font-bold text-slate-900">{value}</p>
            {change !== undefined && (
              <div className="mt-2 flex items-center">
                {trend === 'up' ? (
                  <TrendingUp className="w-4 h-4 text-green-600" />
                ) : trend === 'down' ? (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                ) : null}
                <span className={cn('ml-1 text-sm font-medium', trend === 'up' ? 'text-green-600' : trend === 'down' ? 'text-red-600' : 'text-slate-600')}>
                  {change >= 0 ? '+' : ''}{change.toFixed(1)}%
                </span>
                {changeLabel && (
                  <span className="ml-1 text-sm text-slate-500">{changeLabel}</span>
                )}
              </div>
            )}
          </div>
          <div className={cn('p-3 rounded-lg', iconColor)}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface StatusBadgeProps {
  status: string;
  count: number;
  total: number;
}

export function StatusBadge({ status, count, total }: StatusBadgeProps) {
  const { className, label } = getStatusBadge(status);
  const percentage = total > 0 ? ((count / total) * 100).toFixed(1) : '0';
  
  return (
    <div className="flex items-center justify-between px-4 py-3 hover:bg-slate-50">
      <div className="flex items-center">
        <span className={className}>{label}</span>
      </div>
      <div className="text-right">
        <p className="font-semibold text-slate-900">{formatNumber(count)}</p>
        <p className="text-xs text-slate-500">{percentage}% of total</p>
      </div>
    </div>
  );
}

interface AgingBucketProps {
  label: string;
  value: number;
  percentage: number;
  color: string;
}

export function AgingBucket({ label, value, percentage, color }: AgingBucketProps) {
  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-600">{label}</span>
        <span className="font-medium text-slate-900">{formatCurrency(value)}</span>
      </div>
      <div className="h-2 bg-slate-200 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-500"
          style={{ width: `${percentage}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

interface PayerPerformanceRowProps {
  payer: {
    payer_name: string;
    total_charged: number;
    total_paid: number;
    collection_rate: number;
    denial_rate: number;
    avg_days_to_pay: number;
  };
}

export function PayerPerformanceRow({ payer }: PayerPerformanceRowProps) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-3 font-medium text-slate-900">{payer.payer_name}</td>
      <td className="px-4 py-3 text-slate-600">{formatCurrency(payer.total_charged)}</td>
      <td className="px-4 py-3 text-slate-600">{formatCurrency(payer.total_paid)}</td>
      <td className="px-4 py-3">
        <span className={cn('px-2 py-1 rounded-full text-xs font-medium', payer.collection_rate >= 90 ? 'bg-green-100 text-green-800' : payer.collection_rate >= 70 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800')}>
          {formatPercent(payer.collection_rate)}
        </span>
      </td>
      <td className="px-4 py-3">
        <span className={cn('px-2 py-1 rounded-full text-xs font-medium', payer.denial_rate <= 5 ? 'bg-green-100 text-green-800' : payer.denial_rate <= 15 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800')}>
          {formatPercent(payer.denial_rate)}
        </span>
      </td>
      <td className="px-4 py-3 text-slate-600">{payer.avg_days_to_pay.toFixed(1)} days</td>
    </tr>
  );
}

interface DenialCodeRowProps {
  code: {
    denial_code: string;
    count: number;
    total_denied: number;
    avg_denied: number;
  };
}

export function DenialCodeRow({ code }: DenialCodeRowProps) {
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-3 font-mono font-medium text-slate-900">{code.denial_code}</td>
      <td className="px-4 py-3 text-slate-600">{formatNumber(code.count)}</td>
      <td className="px-4 py-3 text-slate-600">{formatCurrency(code.total_denied)}</td>
      <td className="px-4 py-3 text-slate-600">{formatCurrency(code.avg_denied)}</td>
    </tr>
  );
}