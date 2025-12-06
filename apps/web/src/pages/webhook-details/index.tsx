import { useParams, useNavigate } from 'react-router-dom';
import { useWebhook, useDeleteWebhook, useUpdateWebhook } from '@/hooks/use-webhooks';
import { useJobExecutions } from '@/hooks/use-job-executions';
import type { JobExecution } from '@/types/webhook.types';
import { FadeIn } from '@/components/motion/fade-in';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';
import {
  Pencil,
  Trash2,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Timer,
  Webhook,
  Copy,
  Check,
  PlayCircle,
  CheckCircle,
  RefreshCw,
} from 'lucide-react';
import { Switch } from '@/components/ui/switch';
import { formatDistanceToNow, format } from 'date-fns';
import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import { CartesianGrid, XAxis, YAxis, Bar, BarChart, Cell } from 'recharts';
import { motion, AnimatePresence } from 'motion/react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

// Transform API execution data to frontend format
const transformExecution = (execution: any) => {
  const statusCode =
    execution.response_code ||
    (execution.status === 'success' ? 200 : execution.status === 'failure' ? 500 : 0);
  const isSuccess = statusCode >= 200 && statusCode < 300;
  const timestamp = new Date(execution.created_at);
  const startedAt = execution.started_at ? new Date(execution.started_at) : null;
  const finishedAt = execution.finished_at ? new Date(execution.finished_at) : null;

  // Parse response body if it's a string, otherwise use as-is
  let responseBody = execution.response_body;
  if (responseBody && typeof responseBody === 'string') {
    try {
      // Try to parse as JSON and format it nicely
      const parsed = JSON.parse(responseBody);
      responseBody = JSON.stringify(parsed, null, 2);
    } catch {
      // If not JSON, use as-is
    }
  }

  return {
    id: execution.id,
    timestamp,
    startedAt,
    finishedAt,
    status:
      execution.status === 'success'
        ? 'success'
        : execution.status === 'failure'
          ? 'error'
          : execution.status === 'timed_out'
            ? 'timeout'
            : execution.status === 'queued'
              ? 'queued'
              : execution.status === 'running'
                ? 'running'
                : 'error',
    statusCode,
    duration: execution.duration_ms ?? null,
    attempt: execution.attempt ?? null,
    error: execution.error ?? null,
    response: {
      status: statusCode,
      body: responseBody ?? null,
      headers: {
        'content-type': 'application/json',
      },
    },
  };
};

const WebhookDetailsPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: webhook, isLoading, isError } = useWebhook(id!);
  const deleteWebhook = useDeleteWebhook();
  const updateWebhook = useUpdateWebhook();
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [expandedExecution, setExpandedExecution] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [loadedExecutions, setLoadedExecutions] = useState<JobExecution[]>([]);
  const [totalExecutions, setTotalExecutions] = useState<number>(0);
  const [currentOffset, setCurrentOffset] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const loadMoreRef = useRef<HTMLDivElement>(null);
  const executionsListRef = useRef<HTMLDivElement>(null);
  const hasMoreRef = useRef(true);
  const isLoadingMoreRef = useRef(false);
  const isLoadingMoreExecutionsRef = useRef(false);

  const {
    data: executionsData,
    isLoading: isLoadingExecutions,
    isRefetching: isRefetchingExecutions,
    refetch: refetchExecutions,
  } = useJobExecutions(id, 20, 0);

  // Compute offset for loading more - only load when currentOffset > 0
  const loadMoreOffset = useMemo(() => {
    return currentOffset > 0 ? currentOffset : undefined;
  }, [currentOffset]);

  // Load more executions hook (only enabled when loading more)
  const { data: moreExecutionsData, isLoading: isLoadingMoreExecutions } = useJobExecutions(
    id,
    20,
    loadMoreOffset
  );

  // Keep refs in sync with state
  useEffect(() => {
    hasMoreRef.current = hasMore;
  }, [hasMore]);

  useEffect(() => {
    isLoadingMoreRef.current = isLoadingMore;
  }, [isLoadingMore]);

  useEffect(() => {
    isLoadingMoreExecutionsRef.current = isLoadingMoreExecutions;
  }, [isLoadingMoreExecutions]);

  // Initialize loaded executions when first data loads or on refresh
  useEffect(() => {
    if (executionsData && currentOffset === 0 && loadedExecutions.length === 0) {
      // Only initialize if we don't have loaded executions yet
      setLoadedExecutions(executionsData.data);
      setTotalExecutions(executionsData.meta.total);
      setHasMore(executionsData.data.length === 20);
      setIsLoadingMore(false);
    } else if (executionsData && currentOffset === 0 && isRefreshing) {
      // Force update on refresh even if we have data
      setLoadedExecutions(executionsData.data);
      setTotalExecutions(executionsData.meta.total);
      setHasMore(executionsData.data.length === 20);
      setIsLoadingMore(false);
    }
  }, [executionsData, currentOffset, loadedExecutions.length, isRefreshing]);

  // Append more executions when loading more
  useEffect(() => {
    if (moreExecutionsData && currentOffset > 0 && moreExecutionsData.data.length > 0) {
      setLoadedExecutions((prev) => {
        // Avoid duplicates by checking IDs
        const existingIds = new Set(prev.map((e) => e.id));
        const newExecutions = moreExecutionsData.data.filter((e) => !existingIds.has(e.id));
        return [...prev, ...newExecutions];
      });
      // Don't update totalExecutions - we already have it from the initial load
      setHasMore(moreExecutionsData.data.length === 20);
      setIsLoadingMore(false);
    } else if (moreExecutionsData && currentOffset > 0 && moreExecutionsData.data.length === 0) {
      // No more data available
      setHasMore(false);
      setIsLoadingMore(false);
    }
  }, [moreExecutionsData, currentOffset]);

  // Transform API executions to frontend format
  const executions = useMemo(() => {
    if (loadedExecutions.length === 0) return [];
    return loadedExecutions
      .map(transformExecution)
      .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }, [loadedExecutions]);

  // Load more executions when scrolling to bottom
  const loadMore = useCallback(() => {
    if (!isLoadingMoreRef.current && hasMoreRef.current && !isLoadingMoreExecutionsRef.current) {
      setIsLoadingMore(true);
      setCurrentOffset((prev) => {
        const nextOffset = prev + 20;
        return nextOffset;
      });
    }
  }, []);

  // Intersection Observer for infinite scroll
  useEffect(() => {
    // Only set up observer if we have more data to load
    if (!hasMoreRef.current) {
      return;
    }

    const scrollContainer = executionsListRef.current;
    const triggerElement = loadMoreRef.current;

    if (!scrollContainer || !triggerElement) {
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        const entry = entries[0];
        if (
          entry.isIntersecting &&
          hasMoreRef.current &&
          !isLoadingMoreRef.current &&
          !isLoadingMoreExecutionsRef.current
        ) {
          loadMore();
        }
      },
      {
        root: scrollContainer,
        rootMargin: '100px',
        threshold: 0.01,
      }
    );

    observer.observe(triggerElement);

    return () => {
      observer.disconnect();
    };
  }, [loadMore, executions.length, hasMore]);

  // Reset when webhook ID changes
  useEffect(() => {
    setLoadedExecutions([]);
    setTotalExecutions(0);
    setCurrentOffset(0);
    setHasMore(true);
    setIsLoadingMore(false);
  }, [id]);

  // Prepare chart data - one bar per execution (limit to first 30)
  const chartData = useMemo(() => {
    return executions.slice(0, 30).map((exec, index) => ({
      name: `#${executions.length - index}`,
      duration: exec.duration ?? 0, // Use 0 for chart if duration is null
      status: exec.statusCode >= 200 && exec.statusCode < 300 ? 'success' : 'error',
      statusCode: exec.statusCode,
      timestamp: format(exec.timestamp, 'MMM dd, HH:mm:ss'),
    }));
  }, [executions]);

  // Calculate summary stats
  const summaryStats = useMemo(() => {
    const total = executions.length;
    const success = executions.filter((e) => e.statusCode >= 200 && e.statusCode < 300).length;
    const error = total - success;
    const executionsWithDuration = executions.filter((e) => e.duration !== null);
    const avgDuration =
      executionsWithDuration.length > 0
        ? Math.round(
            executionsWithDuration.reduce((sum, e) => sum + (e.duration ?? 0), 0) /
              executionsWithDuration.length
          )
        : 0;
    const successRate = total > 0 ? Math.round((success / total) * 100) : 0;

    return { total, success, error, avgDuration, successRate };
  }, [executions]);

  const getStatusBadge = (status: string, statusCode: number) => {
    // Handle status-based badges first (for queued, running, etc.)
    if (status === 'queued') {
      return (
        <Badge variant="outline" className="bg-blue-500/10 text-blue-600 border-blue-500/20">
          <Timer className="h-3 w-3 mr-1" />
          Queued
        </Badge>
      );
    }
    if (status === 'running') {
      return (
        <Badge variant="outline" className="bg-purple-500/10 text-purple-600 border-purple-500/20">
          <Timer className="h-3 w-3 mr-1" />
          Running
        </Badge>
      );
    }
    if (status === 'timeout') {
      return (
        <Badge variant="outline" className="bg-orange-500/10 text-orange-600 border-orange-500/20">
          <AlertCircle className="h-3 w-3 mr-1" />
          Timeout
        </Badge>
      );
    }

    // Handle HTTP status code-based badges
    if (statusCode >= 200 && statusCode < 300) {
      return (
        <Badge variant="outline" className="bg-green-500/10 text-green-600 border-green-500/20">
          <CheckCircle2 className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    } else if (statusCode >= 400 && statusCode < 500) {
      return (
        <Badge variant="outline" className="bg-yellow-500/10 text-yellow-600 border-yellow-500/20">
          <AlertCircle className="h-3 w-3 mr-1" />
          {statusCode}
        </Badge>
      );
    } else {
      return (
        <Badge variant="outline" className="bg-red-500/10 text-red-600 border-red-500/20">
          <XCircle className="h-3 w-3 mr-1" />
          {statusCode || 'Error'}
        </Badge>
      );
    }
  };

  const handleDelete = () => {
    if (id) {
      deleteWebhook.mutate(id, {
        onSuccess: () => {
          navigate('/');
        },
      });
    }
  };

  const handleCopy = (text: string, executionId: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(executionId);
    toast('Copied!', {
      description: 'Content copied to clipboard',
    });
    setTimeout(() => setCopiedId(null), 2000);
  };

  // Handle toggle enable/disable
  const handleToggleEnabled = async (newEnabled: boolean) => {
    if (!id) return;
    try {
      await updateWebhook.mutateAsync({
        id,
        data: {
          job: {
            enabled: newEnabled,
          },
        } as any,
      });
      toast(newEnabled ? 'Webhook enabled' : 'Webhook disabled', {
        description: `Webhook has been ${newEnabled ? 'enabled' : 'disabled'}`,
      });
    } catch (error) {
      console.error('Failed to toggle webhook status:', error);
      toast.error('Error', {
        description: 'Failed to update webhook status',
      });
    }
  };

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto space-y-6 max-w-7xl">
          <Skeleton className="h-10 w-32 mb-4" />
          <Skeleton className="h-16 w-full" />
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-24 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Error state
  if (isError || !webhook) {
    return (
      <div className="min-h-screen bg-background p-8 pl-32">
        <div className="container mx-auto max-w-4xl">
          <FadeIn>
            <div className="rounded-lg border border-destructive/50 bg-destructive/5 p-6 text-center">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <h2 className="text-xl font-semibold mb-2">Webhook Not Found</h2>
              <p className="text-sm text-muted-foreground mb-4">
                The webhook you're looking for could not be found.
              </p>
              <Button onClick={() => navigate('/')}>Return to Dashboard</Button>
            </div>
          </FadeIn>
        </div>
      </div>
    );
  }

  const job = webhook.job;

  return (
    <div className="min-h-screen bg-background p-8 pl-32">
      <div className="container mx-auto space-y-6 max-w-7xl">
        {/* Header */}
        <FadeIn>
          <Card className="mb-4 rounded-xl border-border/50 bg-card transition-all shadow-none duration-200 hover:border-border hover:shadow-sm">
            <CardContent className="flex items-center justify-between gap-6 p-4">
              {/* Left Side - Information */}
              <div className="flex items-center gap-4 flex-1 min-w-0">
                <div className="flex-shrink-0 flex items-center justify-center w-10 h-10 rounded-lg bg-primary/10">
                  <Webhook className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-sm text-foreground truncate">
                      {job?.name || 'Unnamed Webhook'}
                    </h3>
                    <span className="text-xs text-muted-foreground">
                      {formatDistanceToNow(new Date(webhook.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5 min-w-0">
                      <code className="truncate font-mono">{webhook.url}</code>
                      <button
                        className="flex-shrink-0 rounded p-0.5 text-muted-foreground opacity-0 transition-all hover:text-foreground group-hover:opacity-100"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCopy(webhook.url, webhook.id);
                        }}
                      >
                        {copiedId === webhook.id ? (
                          <Check className="h-3 w-3" />
                        ) : (
                          <Copy className="h-3 w-3" />
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Side - Actions */}
              <div className="flex items-center gap-3 flex-shrink-0">
                <div className="flex items-center gap-1">
                  {/* Edit Button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => navigate(`/edit/${webhook.id}`)}
                    className="h-9 group"
                  >
                    <Pencil className="h-3.5 w-3.5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </Button>
                  {/* Delete Button */}
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => setDeleteDialogOpen(true)}
                    className="h-9 group"
                  >
                    <Trash2 className="h-3.5 w-3.5 text-muted-foreground group-hover:text-destructive transition-colors" />
                  </Button>
                </div>
                {/* Enable/Disable Toggle */}
                <div className="flex items-center gap-2">
                  <Switch
                    checked={job?.enabled ?? false}
                    onCheckedChange={handleToggleEnabled}
                    disabled={updateWebhook.isPending}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </FadeIn>

        {/* Execution Overview Chart */}
        <FadeIn delay={0.1}>
          <Card className="shadow-none border-border/50 bg-card transition-all duration-200 hover:border-border hover:shadow-sm">
            <CardContent className="p-5">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-foreground">Execution Overview</h3>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Success rate: {summaryStats.successRate}% • Avg response:{' '}
                    {summaryStats.avgDuration}ms
                  </p>
                </div>
                <div className="flex items-center gap-4 text-xs">
                  <div className="flex items-center gap-1.5">
                    <div className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="text-muted-foreground">Success ({summaryStats.success})</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <div className="h-2 w-2 rounded-full bg-red-500" />
                    <span className="text-muted-foreground">Error ({summaryStats.error})</span>
                  </div>
                </div>
              </div>
              <ChartContainer
                config={{
                  success: {
                    label: 'Success',
                    color: 'hsl(142, 71%, 45%)',
                  },
                  error: {
                    label: 'Error',
                    color: 'hsl(0, 84%, 60%)',
                  },
                }}
                className="h-[300px] w-full"
              >
                <BarChart
                  data={chartData}
                  barCategoryGap="20%"
                  margin={{ top: 8, right: 8, bottom: 8, left: 8 }}
                >
                  <CartesianGrid strokeDasharray="3 3" vertical={false} className="stroke-muted" />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    tickMargin={8}
                    width={50}
                    tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                    label={{
                      value: 'ms',
                      angle: -90,
                      position: 'insideLeft',
                      style: { textAnchor: 'middle', fontSize: 11 },
                    }}
                  />
                  <ChartTooltip
                    cursor={false}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div className="rounded-lg border bg-background p-2.5 shadow-sm">
                            <div className="grid gap-1.5">
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Status</span>
                                <Badge
                                  variant="outline"
                                  className={
                                    data.status === 'success'
                                      ? 'bg-green-500/10 text-green-600 border-green-500/20 text-[10px] h-5 px-1.5'
                                      : 'bg-red-500/10 text-red-600 border-red-500/20 text-[10px] h-5 px-1.5'
                                  }
                                >
                                  {data.statusCode}
                                </Badge>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Duration</span>
                                <span className="text-[10px] font-medium">{data.duration}ms</span>
                              </div>
                              <div className="flex items-center justify-between gap-4">
                                <span className="text-[10px] text-muted-foreground">Time</span>
                                <span className="text-[10px] font-medium">{data.timestamp}</span>
                              </div>
                            </div>
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar dataKey="duration" radius={[2, 2, 0, 0]} maxBarSize={24}>
                    {chartData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={
                          entry.status === 'success' ? 'hsl(142, 71%, 45%)' : 'hsl(0, 84%, 60%)'
                        }
                        style={{ opacity: 0.9 }}
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ChartContainer>
            </CardContent>
          </Card>
        </FadeIn>

        {/* Main Content - Execution Logs with Animated Details */}
        <div>
          <motion.div
            className="grid gap-6 relative"
            initial={false}
            animate={{
              gridTemplateColumns: expandedExecution ? '0.3fr 0.7fr' : '1fr',
            }}
            transition={{
              duration: 0.4,
              ease: [0.16, 1, 0.3, 1],
            }}
          >
            {/* Execution Logs List */}
            <motion.div className="min-w-0" layout>
              <FadeIn delay={0.2}>
                <Card className="shadow-none bg-transparent border-none">
                  <CardHeader className="py-4 px-0">
                    <CardTitle>
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <p className="text-sm font-semibold">Execution Logs</p>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            onClick={async () => {
                              setIsRefreshing(true);
                              try {
                                // Reset pagination state first
                                setCurrentOffset(0);
                                setHasMore(true);
                                setIsLoadingMore(false);
                                setLoadedExecutions([]);
                                // Add intentional delay to show spinner animation
                                await new Promise((resolve) => setTimeout(resolve, 400));
                                // Refetch will trigger the initialization effect
                                const result = await refetchExecutions();
                                // Ensure data is set even if refetch returns cached data
                                if (
                                  result.data &&
                                  result.data.data &&
                                  result.data.data.length > 0
                                ) {
                                  setLoadedExecutions(result.data.data);
                                  setTotalExecutions(result.data.meta.total);
                                  setHasMore(result.data.data.length === 20);
                                } else {
                                  setTotalExecutions(0);
                                  setHasMore(false);
                                }
                              } finally {
                                setIsRefreshing(false);
                              }
                            }}
                            disabled={isRefetchingExecutions || isRefreshing}
                            className="h-6 w-6"
                            title="Refresh execution logs"
                          >
                            <RefreshCw
                              className={`h-3.5 w-3.5 text-muted-foreground ${
                                isRefetchingExecutions || isRefreshing ? 'animate-spin' : ''
                              }`}
                            />
                          </Button>
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {isLoadingExecutions
                            ? '...'
                            : `${executions.length} of ${totalExecutions} total executions`}
                        </span>
                      </div>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-0">
                    {isLoadingExecutions ? (
                      <div className="space-y-2 p-4">
                        {[...Array(5)].map((_, i) => (
                          <Skeleton key={i} className="h-16 w-full" />
                        ))}
                      </div>
                    ) : executions.length === 0 ? (
                      <div className="py-8 px-4 text-center text-sm text-muted-foreground">
                        <p className="text-sm">No executions yet</p>
                        <p className="text-xs mt-1">
                          Executions will appear here once the webhook runs
                        </p>
                      </div>
                    ) : (
                      <div
                        ref={executionsListRef}
                        className="max-h-[calc(100vh-200px)] overflow-y-auto scrollbar-primary space-y-2 pr-2"
                      >
                        {executions.map((execution) => (
                          <button
                            key={execution.id}
                            onClick={() =>
                              setExpandedExecution(
                                expandedExecution === execution.id ? null : execution.id
                              )
                            }
                            className={cn(
                              'w-full text-left p-4 border border-border/50 rounded-lg transition-colors hover:bg-muted/50',
                              expandedExecution === execution.id
                                ? 'bg-primary/10 border-primary'
                                : ''
                            )}
                          >
                            <div className="space-y-2">
                              {/* First row: Status, Duration, Timestamp */}
                              <div className="flex items-center gap-2">
                                <div className="flex items-center gap-2 flex-1 min-w-0 flex-wrap">
                                  {getStatusBadge(execution.status, execution.statusCode)}
                                  {execution.duration !== null && (
                                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                                      <Timer className="h-3 w-3" />
                                      {execution.duration}ms
                                    </div>
                                  )}
                                  {execution.attempt !== null && execution.attempt > 1 && (
                                    <Badge
                                      variant="outline"
                                      className="text-[10px] h-4 px-1.5 bg-orange-500/10 text-orange-600 border-orange-500/20 whitespace-nowrap"
                                    >
                                      Attempt {execution.attempt}
                                    </Badge>
                                  )}
                                </div>
                                <div className="flex-shrink-0 text-right">
                                  <p className="text-xs text-muted-foreground">
                                    {formatDistanceToNow(execution.timestamp, { addSuffix: true })}
                                  </p>
                                </div>
                              </div>

                              {/* Second row: Started, Finished times */}
                              {(execution.startedAt || execution.finishedAt) && (
                                <div className="flex items-center gap-3 text-xs text-muted-foreground flex-wrap">
                                  {execution.startedAt && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-[10px]">Started:</span>
                                      <span className="text-[10px] font-mono">
                                        {format(execution.startedAt, 'HH:mm:ss')}
                                      </span>
                                    </div>
                                  )}
                                  {execution.finishedAt && (
                                    <div className="flex items-center gap-1">
                                      <span className="text-[10px]">Finished:</span>
                                      <span className="text-[10px] font-mono">
                                        {format(execution.finishedAt, 'HH:mm:ss')}
                                      </span>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          </button>
                        ))}

                        {/* Load more trigger and shimmer loading */}
                        {hasMore && (
                          <div
                            ref={loadMoreRef}
                            className="py-4 min-h-[40px] flex items-center justify-center"
                          >
                            {isLoadingMore || isLoadingMoreExecutions ? (
                              <div className="space-y-2 w-full">
                                {[...Array(3)].map((_, i) => (
                                  <div
                                    key={`skeleton-${i}`}
                                    className="p-4 border border-border/50 rounded-lg"
                                  >
                                    <Skeleton className="h-4 w-24 mb-2" />
                                    <Skeleton className="h-3 w-full" />
                                    <Skeleton className="h-3 w-3/4 mt-2" />
                                  </div>
                                ))}
                              </div>
                            ) : (
                              <div className="h-10 w-full" />
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </FadeIn>
            </motion.div>

            {/* Right Column - Expanded Execution Details */}
            <AnimatePresence mode="wait">
              {expandedExecution && (
                <motion.div
                  key={expandedExecution}
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 20 }}
                  transition={{
                    duration: 0.4,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                  className="min-w-0"
                  layout
                >
                  {(() => {
                    const execution = executions.find((e) => e.id === expandedExecution);
                    if (!execution) return null;
                    return (
                      <Card className="shadow-none bg-transparent border-none">
                        <CardHeader className="py-4 px-0">
                          <CardTitle className="text-sm font-semibold">Execution Details</CardTitle>
                        </CardHeader>
                        <CardContent className="bg-card rounded-lg p-4 border border-border/50 space-y-4">
                          {/* Detailed Summary Section */}
                          <div className="space-y-4 pb-4 border-b border-border/50">
                            {/* Single Row: Status, Duration, Started, Finished */}
                            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                              {/* Status Card */}
                              <div className="flex flex-col gap-2 p-3 rounded-lg border border-border/50 bg-muted/30">
                                <div className="flex items-center gap-2">
                                  <div className="p-1.5 rounded-md bg-primary/10">
                                    {execution.status === 'success' ? (
                                      <CheckCircle2 className="h-3.5 w-3.5 text-green-600" />
                                    ) : execution.status === 'failure' ? (
                                      <XCircle className="h-3.5 w-3.5 text-red-600" />
                                    ) : execution.status === 'timeout' ? (
                                      <AlertCircle className="h-3.5 w-3.5 text-orange-600" />
                                    ) : (
                                      <AlertCircle className="h-3.5 w-3.5 text-muted-foreground" />
                                    )}
                                  </div>
                                  <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                                    Status
                                  </span>
                                </div>
                                <div className="mt-1">
                                  {getStatusBadge(execution.status, execution.statusCode)}
                                </div>
                              </div>

                              {/* Duration Card */}
                              {execution.duration !== null && (
                                <div className="flex flex-col gap-2 p-3 rounded-lg border border-border/50 bg-muted/30">
                                  <div className="flex items-center gap-2">
                                    <div className="p-1.5 rounded-md bg-purple-500/10">
                                      <Timer className="h-3.5 w-3.5 text-purple-600" />
                                    </div>
                                    <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                                      Duration
                                    </span>
                                  </div>
                                  <div className="mt-1">
                                    <span className="text-sm font-semibold">
                                      {execution.duration}
                                    </span>
                                    <span className="text-xs text-muted-foreground ml-1">ms</span>
                                  </div>
                                </div>
                              )}

                              {/* Started Time */}
                              {execution.startedAt && (
                                <div className="flex flex-col gap-2 p-3 rounded-lg border border-border/50 bg-muted/30">
                                  <div className="flex items-center gap-2">
                                    <div className="p-1.5 rounded-md bg-amber-500/10">
                                      <PlayCircle className="h-3.5 w-3.5 text-amber-600" />
                                    </div>
                                    <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                                      Started
                                    </span>
                                  </div>
                                  <div className="mt-1">
                                    <p className="text-xs font-semibold">
                                      {format(execution.startedAt, 'MMM dd, yyyy')}
                                    </p>
                                    <p className="text-xs text-muted-foreground font-mono mt-0.5">
                                      {format(execution.startedAt, 'HH:mm:ss.SSS')}
                                    </p>
                                  </div>
                                </div>
                              )}

                              {/* Finished Time */}
                              {execution.finishedAt && (
                                <div className="flex flex-col gap-2 p-3 rounded-lg border border-border/50 bg-muted/30">
                                  <div className="flex items-center gap-2">
                                    <div className="p-1.5 rounded-md bg-teal-500/10">
                                      <CheckCircle className="h-3.5 w-3.5 text-teal-600" />
                                    </div>
                                    <span className="text-[10px] font-medium text-muted-foreground uppercase tracking-wide">
                                      Finished
                                    </span>
                                  </div>
                                  <div className="mt-1">
                                    <p className="text-xs font-semibold">
                                      {format(execution.finishedAt, 'MMM dd, yyyy')}
                                    </p>
                                    <p className="text-xs text-muted-foreground font-mono mt-0.5">
                                      {format(execution.finishedAt, 'HH:mm:ss.SSS')}
                                    </p>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>

                          {/* Error message if failed */}
                          {execution.error && (
                            <div className="p-3 rounded bg-destructive/5 border border-destructive/20">
                              <p className="text-xs font-semibold text-destructive mb-1">Error:</p>
                              <p className="text-xs text-destructive break-words whitespace-pre-wrap">
                                {execution.error}
                              </p>
                            </div>
                          )}

                          <Tabs defaultValue="headers" className="w-full">
                            <TabsList className="grid w-full grid-cols-2">
                              <TabsTrigger value="headers">Headers</TabsTrigger>
                              <TabsTrigger value="body">Body</TabsTrigger>
                            </TabsList>

                            <TabsContent value="headers" className="mt-4">
                              {execution.response.headers &&
                              Object.keys(execution.response.headers).length > 0 ? (
                                <div className="space-y-2 max-h-[400px] overflow-y-auto">
                                  {Object.entries(execution.response.headers).map(
                                    ([key, value]) => (
                                      <div
                                        key={key}
                                        className="flex flex-col gap-1 p-2 rounded border border-border/50 bg-muted/30"
                                      >
                                        <div className="flex items-center justify-between gap-2">
                                          <p className="text-xs font-semibold text-muted-foreground break-all">
                                            {key}
                                          </p>
                                          <Button
                                            variant="ghost"
                                            size="sm"
                                            onClick={() =>
                                              handleCopy(`${key}: ${value}`, execution.id)
                                            }
                                            className="flex-shrink-0 h-6 w-6 p-0"
                                          >
                                            {copiedId === execution.id ? (
                                              <Check className="h-3 w-3" />
                                            ) : (
                                              <Copy className="h-3 w-3" />
                                            )}
                                          </Button>
                                        </div>
                                        <code className="text-xs break-all font-mono text-foreground bg-background p-2 rounded border border-border/30">
                                          {String(value)}
                                        </code>
                                      </div>
                                    )
                                  )}
                                </div>
                              ) : (
                                <p className="text-sm text-muted-foreground text-center py-4">
                                  No headers
                                </p>
                              )}
                            </TabsContent>

                            <TabsContent value="body" className="mt-4">
                              {execution.response.body ? (
                                <div className="relative border border-border/50 rounded-lg overflow-hidden">
                                  <div className="absolute top-2 right-2 z-10">
                                    <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-7 w-7 p-0 bg-background/80 backdrop-blur-sm"
                                      onClick={() =>
                                        handleCopy(execution.response.body, execution.id)
                                      }
                                    >
                                      {copiedId === execution.id ? (
                                        <Check className="h-3.5 w-3.5" />
                                      ) : (
                                        <Copy className="h-3.5 w-3.5" />
                                      )}
                                    </Button>
                                  </div>
                                  <pre className="max-h-[400px] overflow-auto p-4 text-xs bg-muted">
                                    <code className="language-json break-words whitespace-pre-wrap">
                                      {(() => {
                                        try {
                                          return JSON.stringify(
                                            JSON.parse(execution.response.body),
                                            null,
                                            2
                                          );
                                        } catch {
                                          return execution.response.body;
                                        }
                                      })()}
                                    </code>
                                  </pre>
                                </div>
                              ) : (
                                <p className="text-sm text-center text-muted-foreground py-4">
                                  No body
                                </p>
                              )}
                            </TabsContent>
                          </Tabs>
                        </CardContent>
                      </Card>
                    );
                  })()}
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete webhook?</AlertDialogTitle>
            <AlertDialogDescription>
              This action cannot be undone. The webhook will be permanently removed and will stop
              sending scheduled requests.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteWebhook.isPending ? 'Deleting...' : 'Delete'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default WebhookDetailsPage;
